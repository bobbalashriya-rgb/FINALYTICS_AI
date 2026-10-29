import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from companies.models import Company
from companies.services import CompanyService
from companies.exceptions import CompanyNotFoundError
from core.integrations.marketping.exceptions import MarketPingConnectionError


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_company_resolution_and_persistence():
    """Verify CompanyService resolves candidate from provider and saves in PostgreSQL."""
    mock_provider = MagicMock()
    mock_provider.resolve_company.return_value = [
        {
            "slug": "infosys",
            "name": "INFOSYS LIMITED",
            "nse_symbol": "INFY",
            "bse_code": "500209",
            "url": "https://marketping.in/companies/infosys",
        }
    ]

    service = CompanyService(provider=mock_provider)
    company = service.get_or_resolve_company("INFY")

    assert company.ticker == "INFY"
    assert company.slug == "infosys"
    assert company.name == "INFOSYS LIMITED"
    assert Company.objects.filter(ticker="INFY").exists()

    # Second call should read from local DB without querying provider
    company_cached = service.get_or_resolve_company("INFY")
    assert company_cached.id == company.id
    assert mock_provider.resolve_company.call_count == 1


@pytest.mark.django_db
def test_company_resolution_not_found():
    """Verify CompanyNotFoundError is raised when provider returns no matches."""
    mock_provider = MagicMock()
    mock_provider.resolve_company.return_value = []

    service = CompanyService(provider=mock_provider)
    with pytest.raises(CompanyNotFoundError):
        service.get_or_resolve_company("NONEXISTENT_TICKER_XYZ")


@pytest.mark.django_db
def test_company_detail_api_success(api_client):
    """Test GET /api/companies/{ticker}/ returns 200 with serialized company."""
    Company.objects.create(
        ticker="TCS",
        slug="tcs",
        name="Tata Consultancy Services Limited",
        source_url="https://marketping.in/companies/tcs",
    )

    url = reverse("company-detail", kwargs={"ticker": "TCS"})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["ticker"] == "TCS"
    assert data["slug"] == "tcs"
    assert data["name"] == "Tata Consultancy Services Limited"


@pytest.mark.django_db
def test_company_detail_api_not_found(api_client):
    """Test GET /api/companies/{ticker}/ returns 404 when company cannot be resolved."""
    with patch("companies.services.get_financial_data_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.resolve_company.return_value = []
        mock_get_provider.return_value = mock_provider

        url = reverse("company-detail", kwargs={"ticker": "UNKNOWN_TICKER"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "company_not_found"


@pytest.mark.django_db
def test_company_detail_api_upstream_error(api_client):
    """Test GET /api/companies/{ticker}/ returns 503 when MarketPing MCP is unreachable."""
    with patch("companies.services.get_financial_data_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.resolve_company.side_effect = MarketPingConnectionError("MCP timeout")
        mock_get_provider.return_value = mock_provider

        url = reverse("company-detail", kwargs={"ticker": "RELIANCE"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "upstream_service_error"
