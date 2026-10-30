import hashlib
import logging
import re
from typing import Any, Dict, List, Optional
from django.utils import timezone
from django.db import transaction

from documents.models import FinancialDocument, DocumentPage
from core.integrations import get_financial_data_provider

logger = logging.getLogger(__name__)


def normalize_financial_text(text: str) -> str:
    """
    Normalizes text while preserving financial tables, currency symbols, and line breaks.
    Replaces non-standard whitespace and special dashes while preserving tabular columns.
    """
    if not text:
        return ""

    # Replace non-breaking spaces, zero-width characters
    normalized = text.replace("\u00a0", " ").replace("\ufeff", "").replace("\u200b", "")

    # Normalize special unicode hyphens and quotes to standard ASCII equivalents
    normalized = normalized.replace("\u2013", "-").replace("\u2014", "-")
    normalized = normalized.replace("\u2018", "'").replace("\u2019", "'")
    normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')

    # Remove non-printable control characters except newline and tab
    normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", normalized)

    # Strip trailing whitespace on each line, but preserve table indentation and empty lines
    lines = [line.rstrip() for line in normalized.splitlines()]
    return "\n".join(lines).strip()


def compute_content_hash(text: str) -> str:
    """Computes SHA-256 hash of the normalized text for idempotency."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentIngestionService:
    """
    Service responsible for retrieving document page content via MarketPing MCP,
    normalizing extracted financial text, and storing pages idempotently in PostgreSQL.
    """

    # MarketPing MCP allows at most 12 pages per read_pages invocation
    MAX_PAGES_PER_MCP_CALL = 12

    def __init__(self, provider=None):
        self.provider = provider or get_financial_data_provider()

    def ingest_document(
        self,
        document: FinancialDocument,
        page_from: Optional[int] = None,
        page_to: Optional[int] = None,
        max_batch_pages: int = 24,
        ingest_all: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingests page content for a financial document.
        Supports:
          - Full ingestion up to total_pages (ingest_all=True)
          - Automatic resumption from the last ingested page
          - Specific page ranges (page_from, page_to)
        """
        total_doc_pages = max(1, document.total_pages)

        # 1. Determine starting page
        if page_from is None:
            # Auto-continue from the next un-ingested page
            last_ingested = (
                document.pages.order_by("-page_number")
                .values_list("page_number", flat=True)
                .first()
            )
            page_from = (last_ingested or 0) + 1
        else:
            page_from = max(1, min(page_from, total_doc_pages))

        # 2. Determine ending page
        if ingest_all:
            page_to = total_doc_pages
        elif page_to is not None:
            page_to = max(page_from, min(page_to, total_doc_pages))
        else:
            page_to = min(total_doc_pages, page_from + max_batch_pages - 1)

        # If already fully ingested or requested range is past total pages
        if page_from > total_doc_pages:
            total_ingested = document.pages.count()
            is_full = total_ingested >= total_doc_pages
            status_val = "completed" if is_full else "partial"
            if document.ingestion_status != status_val:
                document.ingestion_status = status_val
                document.save(update_fields=["ingestion_status", "updated_at"])

            return {
                "document_id": document.id,
                "external_id": document.external_id,
                "title": document.title,
                "status": status_val,
                "is_full_ingestion": is_full,
                "pages_ingested_in_request": 0,
                "total_ingested_pages": total_ingested,
                "total_document_pages": total_doc_pages,
                "page_range": {"requested_from": page_from, "requested_to": total_doc_pages},
                "ingested_at": document.ingested_at.isoformat() if document.ingested_at else None,
                "message": "All pages for this document have already been processed.",
            }

        document.ingestion_status = "in_progress"
        document.save(update_fields=["ingestion_status", "updated_at"])

        ingested_in_this_run = 0

        try:
            current_start = page_from
            while current_start <= page_to:
                current_end = min(
                    page_to, current_start + self.MAX_PAGES_PER_MCP_CALL - 1
                )
                logger.info(
                    "Fetching pages %d to %d (target: %d) for document %s (%s)",
                    current_start,
                    current_end,
                    page_to,
                    document.external_id,
                    document.title,
                )

                response = self.provider.read_pages(
                    doc_id=document.external_id,
                    page_from=current_start,
                    page_to=current_end,
                )

                raw_pages = []
                if isinstance(response, dict) and "pages" in response:
                    raw_pages = response["pages"]
                elif isinstance(response, list):
                    raw_pages = response

                with transaction.atomic():
                    for page_item in raw_pages:
                        if not isinstance(page_item, dict):
                            continue

                        pg_num = page_item.get("page")
                        raw_content = page_item.get("text", "")
                        if pg_num is None:
                            continue

                        normalized = normalize_financial_text(raw_content)
                        chash = compute_content_hash(normalized)
                        char_cnt = len(normalized)
                        word_cnt = len(normalized.split())

                        # Upsert page idempotently
                        DocumentPage.objects.update_or_create(
                            document=document,
                            page_number=pg_num,
                            defaults={
                                "content": normalized,
                                "content_hash": chash,
                                "char_count": char_cnt,
                                "word_count": word_cnt,
                            },
                        )
                        ingested_in_this_run += 1

                current_start = current_end + 1

            # Update document status
            total_ingested = document.pages.count()
            document.ingested_pages_count = total_ingested
            document.ingested_at = timezone.now()
            document.last_error = None

            # Distinguish full vs partial ingestion
            if total_ingested >= total_doc_pages or page_to >= total_doc_pages:
                document.ingestion_status = "completed"
            else:
                document.ingestion_status = "partial"

            document.save(
                update_fields=[
                    "ingestion_status",
                    "ingested_pages_count",
                    "ingested_at",
                    "last_error",
                    "updated_at",
                ]
            )

            return {
                "document_id": document.id,
                "external_id": document.external_id,
                "title": document.title,
                "status": document.ingestion_status,
                "is_full_ingestion": document.ingestion_status == "completed",
                "pages_ingested_in_request": ingested_in_this_run,
                "total_ingested_pages": total_ingested,
                "total_document_pages": total_doc_pages,
                "page_range": {
                    "requested_from": page_from,
                    "requested_to": page_to,
                },
                "ingested_at": document.ingested_at.isoformat() if document.ingested_at else None,
            }

        except Exception as exc:
            logger.exception(
                "Ingestion failed for document %s: %s", document.external_id, exc
            )
            document.ingestion_status = "failed"
            document.last_error = str(exc)
            document.save(
                update_fields=["ingestion_status", "last_error", "updated_at"]
            )
            raise exc
