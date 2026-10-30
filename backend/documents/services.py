import datetime
import logging
from typing import List, Optional

from companies.models import Company
from documents.models import FinancialDocument
from core.integrations import get_financial_data_provider

logger = logging.getLogger(__name__)


def parse_iso_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """Safely parse YYYY-MM-DD date string or return None."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.date.fromisoformat(date_str.strip())
    except (ValueError, TypeError):
        return None


class DocumentDiscoveryService:
    """
    Business service orchestrating financial report discovery, metadata normalization,
    and persistent storage.
    """

    def __init__(self, provider=None):
        self.provider = provider or get_financial_data_provider()

    def discover_and_sync_documents(
        self, company: Company, doc_type: Optional[str] = None
    ) -> List[FinancialDocument]:
        """
        Discovers available financial reports from MarketPing for the company,
        normalizes metadata, and saves them to PostgreSQL without duplicates.
        """
        logger.info(
            "Discovering documents for %s (%s) [doc_type filter: %s]",
            company.ticker,
            company.slug,
            doc_type or "all",
        )
        raw_documents = self.provider.list_documents(
            company=company.slug, doc_type=doc_type
        )

        synced_documents = []

        if not raw_documents or not isinstance(raw_documents, list):
            return synced_documents

        for item in raw_documents:
            if not isinstance(item, dict):
                continue

            external_id = item.get("id")
            if not external_id:
                continue

            d_type = item.get("doc_type") or "other"
            title = item.get("title") or "Financial Document"
            fiscal_period = item.get("filed_fy_quarter")
            period_end = parse_iso_date(item.get("period_end"))
            doc_date = parse_iso_date(item.get("doc_date"))
            pages = item.get("pages") or 1
            navigable = item.get("navigable", True)

            source_ref = f"https://marketping.in/companies/{company.slug}"

            # Upsert document by unique external_id to eliminate duplicates
            doc, _ = FinancialDocument.objects.update_or_create(
                external_id=external_id,
                defaults={
                    "company": company,
                    "doc_type": d_type,
                    "title": title,
                    "fiscal_period": fiscal_period,
                    "period_end_date": period_end,
                    "filing_date": doc_date,
                    "total_pages": int(pages),
                    "is_navigable": bool(navigable),
                    "source_reference": source_ref,
                },
            )
            synced_documents.append(doc)

        return synced_documents

    def get_available_documents(
        self,
        company: Company,
        doc_type: Optional[str] = None,
        sync: bool = True,
    ):
        """
        Returns available documents from local DB, optionally syncing with provider first.
        """
        # If DB has no documents for this company or sync requested, sync from provider
        has_existing = FinancialDocument.objects.filter(company=company).exists()
        if sync or not has_existing:
            try:
                self.discover_and_sync_documents(company=company, doc_type=doc_type)
            except Exception as exc:
                logger.warning(
                    "Live document sync encountered error, falling back to local DB: %s",
                    exc,
                )
                if not has_existing:
                    raise exc

        queryset = FinancialDocument.objects.filter(company=company)
        if doc_type:
            queryset = queryset.filter(doc_type__iexact=doc_type)

        return queryset
