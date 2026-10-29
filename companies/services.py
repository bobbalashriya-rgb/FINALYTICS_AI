import logging
from typing import Optional

from companies.models import Company
from companies.exceptions import CompanyNotFoundError
from core.integrations import get_financial_data_provider

logger = logging.getLogger(__name__)


class CompanyService:
    """
    Business service orchestrating company identification, resolution, and persistence.
    """

    def __init__(self, provider=None):
        self.provider = provider or get_financial_data_provider()

    def get_or_resolve_company(
        self, query: str, force_refresh: bool = False
    ) -> Company:
        """
        Retrieves a company from local storage or resolves it via the financial data provider.
        """
        clean_query = query.strip()
        if not clean_query:
            raise CompanyNotFoundError("A company ticker or name must be provided.")

        # 1. Check local database first if refresh is not forced
        if not force_refresh:
            existing = (
                Company.objects.filter(ticker__iexact=clean_query).first()
                or Company.objects.filter(slug__iexact=clean_query.lower()).first()
            )
            if existing:
                return existing

        # 2. Resolve via provider
        logger.info("Resolving company candidate via provider for query: %s", clean_query)
        matches = self.provider.resolve_company(clean_query)

        if not matches or not isinstance(matches, list) or len(matches) == 0:
            raise CompanyNotFoundError(
                f"No company matching '{clean_query}' could be found or resolved."
            )

        # 3. Pick the best matching candidate
        # Look for exact ticker match (case-insensitive) or slug match first
        best_candidate = None
        for candidate in matches:
            ticker = candidate.get("nse_symbol") or candidate.get("ticker")
            slug = candidate.get("slug")
            if ticker and ticker.upper() == clean_query.upper():
                best_candidate = candidate
                break
            if slug and slug.lower() == clean_query.lower():
                best_candidate = candidate
                break

        if not best_candidate:
            best_candidate = matches[0]

        ticker = (
            best_candidate.get("nse_symbol")
            or best_candidate.get("ticker")
            or best_candidate.get("slug", "").upper()
        )
        slug = best_candidate.get("slug")
        name = best_candidate.get("name") or ticker

        if not slug or not ticker:
            raise CompanyNotFoundError(
                f"Resolved candidate for '{clean_query}' missing valid slug or ticker."
            )

        # 4. Save or update company in persistent PostgreSQL storage
        company, _ = Company.objects.update_or_create(
            slug=slug.lower(),
            defaults={
                "name": name,
                "ticker": ticker.upper(),
                "bse_code": best_candidate.get("bse_code"),
                "source_url": best_candidate.get("url"),
            },
        )
        return company
