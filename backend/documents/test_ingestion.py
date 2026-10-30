import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from companies.models import Company
from documents.models import FinancialDocument, DocumentPage
from documents.ingestion import (
    DocumentIngestionService,
    compute_content_hash,
    normalize_financial_text,
)
from core.integrations.marketping.exceptions import MarketPingConnectionError


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


@pytest.fixture
def sample_document(db, sample_company):
    return FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-ec-100",
        doc_type="earnings_call_transcript",
        title="Q2 Earnings Call Transcript",
        fiscal_period="FY27 Q2",
        total_pages=2,
    )


def test_normalize_financial_text():
    """Verify text normalization preserves tabular layout while cleaning unicode whitespace."""
    raw = "Revenue:\t  INR 45,000 Cr \u00a0\nOperating Margin:\t 21.5% \u2013 22.0% \n \n"
    normalized = normalize_financial_text(raw)

    assert "INR 45,000 Cr" in normalized
    assert "21.5% - 22.0%" in normalized
    assert "\u00a0" not in normalized


def test_compute_content_hash():
    """Verify content hash produces stable SHA-256 hash."""
    h1 = compute_content_hash("Financial performance for FY26")
    h2 = compute_content_hash("Financial performance for FY26")
    h3 = compute_content_hash("Different text")

    assert len(h1) == 64
    assert h1 == h2
    assert h1 != h3


@pytest.mark.django_db
def test_document_ingestion_service_success(sample_document):
    """Verify document ingestion fetches pages, stores DocumentPage records, and updates status."""
    mock_provider = MagicMock()
    mock_provider.read_pages.return_value = {
        "pages": [
            {"page": 1, "text": "Page 1 Transcript Content: Management Remarks"},
            {"page": 2, "text": "Page 2 Transcript Content: Q&A Session"},
        ]
    }

    service = DocumentIngestionService(provider=mock_provider)
    result = service.ingest_document(
        document=sample_document, page_from=1, page_to=2
    )

    assert result["status"] == "completed"
    assert result["is_full_ingestion"] is True
    assert result["total_ingested_pages"] == 2
    assert DocumentPage.objects.filter(document=sample_document).count() == 2

    p1 = DocumentPage.objects.get(document=sample_document, page_number=1)
    assert "Management Remarks" in p1.content
    assert p1.char_count > 0

    # Test idempotency: re-ingesting the exact same pages should not create duplicates
    service.ingest_document(document=sample_document, page_from=1, page_to=2)
    assert DocumentPage.objects.filter(document=sample_document).count() == 2


@pytest.mark.django_db
def test_partial_ingestion_distinction(sample_company):
    """Verify partial ingestion status when only a subset of pages are retrieved."""
    large_doc = FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-ar-large",
        doc_type="annual_report",
        title="Annual Report 2026",
        total_pages=350,
    )

    mock_provider = MagicMock()
    mock_provider.read_pages.return_value = {
        "pages": [{"page": 1, "text": "First page text"}]
    }

    service = DocumentIngestionService(provider=mock_provider)
    result = service.ingest_document(
        document=large_doc, page_from=1, page_to=1
    )

    assert result["status"] == "partial"
    assert result["is_full_ingestion"] is False
    assert result["total_ingested_pages"] == 1
    assert result["total_document_pages"] == 350


@pytest.mark.django_db
def test_ingest_all_and_auto_continuation(sample_company):
    """Verify ingest_all=True fetches all remaining pages to completion."""
    doc = FinancialDocument.objects.create(
        company=sample_company,
        external_id="doc-transcript-full",
        doc_type="earnings_call_transcript",
        title="Transcript",
        total_pages=24,
    )

    mock_provider = MagicMock()
    # Batch 1 (1-12), Batch 2 (13-24)
    mock_provider.read_pages.side_effect = [
        {"pages": [{"page": i, "text": f"Page {i}"} for i in range(1, 13)]},
        {"pages": [{"page": i, "text": f"Page {i}"} for i in range(13, 25)]},
    ]

    service = DocumentIngestionService(provider=mock_provider)
    result = service.ingest_document(document=doc, ingest_all=True)

    assert result["status"] == "completed"
    assert result["is_full_ingestion"] is True
    assert result["total_ingested_pages"] == 24
    assert DocumentPage.objects.filter(document=doc).count() == 24


@pytest.mark.django_db
def test_document_ingest_api_success(api_client, sample_company, sample_document):
    """Test POST /api/companies/{ticker}/documents/{document_id}/ingest/ returns 200."""
    with patch(
        "documents.ingestion.get_financial_data_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.read_pages.return_value = {
            "pages": [
                {"page": 1, "text": "Audited standalone results"},
                {"page": 2, "text": "Audited consolidated results"},
            ]
        }
        mock_get_provider.return_value = mock_provider

        url = reverse(
            "document-ingest",
            kwargs={"ticker": "INFY", "document_id": sample_document.id},
        )
        response = api_client.post(
            url,
            data={"page_from": 1, "page_to": 2},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["document_id"] == sample_document.id
        assert data["status"] == "completed"
        assert data["pages_ingested_in_request"] == 2


@pytest.mark.django_db
def test_document_ingest_api_by_external_uuid(api_client, sample_company, sample_document):
    """Test POST ingest endpoint accepts MarketPing external UUID string."""
    with patch(
        "documents.ingestion.get_financial_data_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.read_pages.return_value = {
            "pages": [{"page": 1, "text": "Audited balance sheet"}]
        }
        mock_get_provider.return_value = mock_provider

        url = reverse(
            "document-ingest",
            kwargs={"ticker": "INFY", "document_id": sample_document.external_id},
        )
        response = api_client.post(url, data={"page_from": 1, "page_to": 1}, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["external_id"] == sample_document.external_id


@pytest.mark.django_db
def test_document_ingest_api_not_found(api_client, sample_company):
    """Test 404 response when attempting to ingest non-existent document."""
    url = reverse(
        "document-ingest",
        kwargs={"ticker": "INFY", "document_id": "non-existent-doc-id"},
    )
    response = api_client.post(url, data={}, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "document_not_found"


@pytest.mark.django_db
def test_document_ingest_api_upstream_error(api_client, sample_company, sample_document):
    """Test 503 response when MarketPing MCP fails during page retrieval."""
    with patch(
        "documents.ingestion.get_financial_data_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.read_pages.side_effect = MarketPingConnectionError("Connection timeout")
        mock_get_provider.return_value = mock_provider

        url = reverse(
            "document-ingest",
            kwargs={"ticker": "INFY", "document_id": sample_document.id},
        )
        response = api_client.post(url, data={}, format="json")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "upstream_service_error"


@pytest.mark.django_db
def test_document_pages_list_api(api_client, sample_company, sample_document):
    """Test GET /api/companies/{ticker}/documents/{document_id}/pages/ returns stored content."""
    DocumentPage.objects.create(
        document=sample_document,
        page_number=1,
        content="Key business highlights and margin growth.",
        content_hash="abc123hash",
        char_count=43,
        word_count=6,
    )

    url = reverse(
        "document-pages-list",
        kwargs={"ticker": "INFY", "document_id": sample_document.id},
    )
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_stored_pages"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["page_number"] == 1
    assert "margin growth" in data["results"][0]["content"]
