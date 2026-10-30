import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from companies.models import Company
from documents.models import FinancialDocument
from documents.services import DocumentDiscoveryService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_company(db):
    return Company.objects.create(
        ticker="INFY",
        slug="infosys",
        name="INFOSYS LIMITED",
    )


@pytest.mark.django_db
def test_document_discovery_normalization_and_deduplication(sample_company):
    """Verify metadata normalization and handling of duplicates and missing dates."""
    mock_provider = MagicMock()
    mock_provider.list_documents.return_value = [
        {
            "id": "doc-uuid-1",
            "doc_type": "annual_report",
            "title": "Annual Report",
            "period_end": "2026-03-31",
            "doc_date": "2026-05-15",
            "filed_fy_quarter": "FY26",
            "pages": 350,
            "navigable": True,
        },
        {
            "id": "doc-uuid-2",
            "doc_type": "earnings_call_transcript",
            "title": "Earnings Call Transcript",
            "period_end": None,  # Missing period end
            "doc_date": "2026-07-20",
            "filed_fy_quarter": None,
            "pages": 45,
            "navigable": True,
        },
    ]

    service = DocumentDiscoveryService(provider=mock_provider)
    docs = service.discover_and_sync_documents(sample_company)

    assert len(docs) == 2
    assert FinancialDocument.objects.count() == 2

    doc1 = FinancialDocument.objects.get(external_id="doc-uuid-1")
    assert doc1.doc_type == "annual_report"
    assert str(doc1.period_end_date) == "2026-03-31"
    assert doc1.fiscal_period == "FY26"
    assert doc1.total_pages == 350

    doc2 = FinancialDocument.objects.get(external_id="doc-uuid-2")
    assert doc2.period_end_date is None
    assert doc2.fiscal_period is None

    # Re-syncing the same documents should update rather than duplicate
    service.discover_and_sync_documents(sample_company)
    assert FinancialDocument.objects.count() == 2


@pytest.mark.django_db
def test_company_available_documents_api(api_client, sample_company):
    """Test GET /api/companies/{ticker}/documents/available/ returns normalized reports."""
    FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-ar-2026",
        doc_type="annual_report",
        title="Annual Report 2026",
        period_end_date="2026-03-31",
        total_pages=300,
    )
    FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-ec-q1",
        doc_type="earnings_call_transcript",
        title="Earnings Call Q1",
        fiscal_period="FY27 Q1",
        total_pages=40,
    )

    url = reverse("company-documents-available", kwargs={"ticker": "INFY"})
    # Query with sync=false to read existing records
    response = api_client.get(f"{url}?sync=false")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["company"]["ticker"] == "INFY"
    assert data["total"] == 2
    assert len(data["results"]) == 2


@pytest.mark.django_db
def test_company_available_documents_filter_by_type(api_client, sample_company):
    """Test filtering documents by doc_type query parameter."""
    FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-ar-1",
        doc_type="annual_report",
        title="Annual Report",
    )
    FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-ec-1",
        doc_type="earnings_call_transcript",
        title="Earnings Transcript",
    )

    url = reverse("company-documents-available", kwargs={"ticker": "INFY"})
    response = api_client.get(f"{url}?sync=false&doc_type=annual_report")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["doc_type"] == "annual_report"


@pytest.mark.django_db
def test_company_available_documents_not_found(api_client):
    """Test 404 response when querying documents for an invalid company."""
    with patch("companies.services.get_financial_data_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.resolve_company.return_value = []
        mock_get_provider.return_value = mock_provider

        url = reverse("company-documents-available", kwargs={"ticker": "NONEXISTENT"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "company_not_found"
