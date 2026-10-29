import pytest
from rest_framework import status
from rest_framework.test import APIClient

from companies.models import Company
from documents.models import FinancialDocument, DocumentPage, DocumentChunk
from documents.chunking import FinancialDocumentChunker, DocumentIndexingService
from core.embeddings.providers import DeterministicLocalEmbeddingProvider


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_company(db):
    return Company.objects.create(
        ticker="TCS",
        slug="tcs",
        name="Tata Consultancy Services Limited",
    )


@pytest.fixture
def sample_document(db, sample_company):
    return FinancialDocument.objects.create(
        company=sample_company,
        external_id="uuid-tcs-ar-2026",
        doc_type="annual_report",
        title="Annual Report 2026",
        fiscal_period="FY26",
        period_end_date="2026-03-31",
        total_pages=100,
        ingestion_status="completed",
        ingested_pages_count=2,
    )


@pytest.fixture
def sample_pages(db, sample_document):
    p1 = DocumentPage.objects.create(
        document=sample_document,
        page_number=1,
        content=(
            "MANAGEMENT DISCUSSION AND ANALYSIS\n\n"
            "The Indian IT services industry demonstrated resilient demand in FY26. "
            "Digital transformation and enterprise cloud adoption accelerated across BFS and retail verticals. "
            "Operating margins remained healthy at 24.5% despite macroeconomic headwinds in European markets."
        ),
        content_hash="hash-p1",
        char_count=280,
        word_count=40,
    )
    p2 = DocumentPage.objects.create(
        document=sample_document,
        page_number=2,
        content=(
            "BALANCE SHEET AS AT MARCH 31, 2026\n\n"
            "Total Assets: INR 1,45,000 Crores\n"
            "Cash and cash equivalents: INR 18,500 Crores\n"
            "Total Liabilities: INR 35,000 Crores\n"
            "Shareholder Equity: INR 1,10,000 Crores"
        ),
        content_hash="hash-p2",
        char_count=180,
        word_count=25,
    )
    return [p1, p2]


def test_section_aware_chunker_detects_headings(sample_pages):
    """Test chunker splits pages into chunks and detects section headings."""
    chunker = FinancialDocumentChunker(target_chunk_chars=200, overlap_chars=30)
    chunks = chunker.chunk_document_pages(sample_pages)

    assert len(chunks) >= 2
    assert chunks[0]["page_start"] == 1
    assert "MANAGEMENT DISCUSSION AND ANALYSIS" in chunks[0]["section_heading"]
    assert any("BALANCE SHEET" in c["section_heading"] for c in chunks)


@pytest.mark.django_db
def test_document_indexing_service_and_idempotency(sample_document, sample_pages):
    """Test indexing generates chunks, computes embeddings, and skips duplicate chunks on rerun."""
    chunker = FinancialDocumentChunker(target_chunk_chars=200, overlap_chars=30)
    provider = DeterministicLocalEmbeddingProvider(dimension=128)
    service = DocumentIndexingService(chunker=chunker, embedding_provider=provider)

    # 1. Initial indexing
    result = service.index_document(sample_document)
    assert result["chunks_processed"] >= 2
    assert result["chunks_indexed"] == result["chunks_processed"]
    assert result["chunks_skipped"] == 0
    assert result["embedding_dimension"] == 128
    assert DocumentChunk.objects.filter(document=sample_document).count() == result["chunks_indexed"]

    # Verify traceable metadata on stored chunk
    first_chunk = DocumentChunk.objects.filter(document=sample_document).first()
    assert len(first_chunk.embedding) == 128
    assert first_chunk.metadata["company_ticker"] == "TCS"
    assert first_chunk.metadata["fiscal_period"] == "FY26"
    assert first_chunk.page_start >= 1

    # 2. Re-indexing without changes must skip all chunks (idempotent)
    reindex_result = service.index_document(sample_document, force_reindex=False)
    assert reindex_result["chunks_indexed"] == 0
    assert reindex_result["chunks_skipped"] == result["chunks_processed"]

    # 3. Force re-indexing must reprocess
    force_result = service.index_document(sample_document, force_reindex=True)
    assert force_result["chunks_indexed"] == result["chunks_processed"]
    assert force_result["chunks_skipped"] == 0


@pytest.mark.django_db
def test_index_api_document_not_found(api_client):
    """Test indexing a nonexistent document returns 404."""
    url = "/api/documents/nonexistent-doc-id/index/"
    response = api_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "document_not_found"


@pytest.mark.django_db
def test_index_api_no_pages_returns_400(api_client, sample_company):
    """Test indexing a document with 0 ingested pages returns 400."""
    empty_doc = FinancialDocument.objects.create(
        company=sample_company,
        external_id="uuid-empty-doc",
        doc_type="financial_results",
        title="Q3 Results",
    )
    url = f"/api/documents/{empty_doc.id}/index/"
    response = api_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "indexing_validation_error"


@pytest.mark.django_db
def test_index_api_success_and_chunks_list(api_client, sample_document, sample_pages):
    """Test POST /api/documents/{document_id}/index/ and GET /api/documents/{document_id}/chunks/."""
    url = f"/api/documents/{sample_document.id}/index/"
    response = api_client.post(
        url,
        {"force_reindex": False, "target_chunk_chars": 500, "overlap_chars": 50},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["document_id"] == sample_document.id
    assert data["chunks_indexed"] > 0
    assert data["chunks_skipped"] == 0

    # Verify GET chunks endpoint
    chunks_url = f"/api/documents/{sample_document.id}/chunks/"
    chunks_resp = api_client.get(chunks_url)
    assert chunks_resp.status_code == status.HTTP_200_OK
    chunks_data = chunks_resp.json()
    assert chunks_data["document_id"] == sample_document.id
    assert len(chunks_data["results"]) == data["chunks_indexed"]

    # Verify company-scoped indexing endpoint alias
    company_index_url = f"/api/companies/TCS/documents/{sample_document.id}/index/"
    c_resp = api_client.post(company_index_url, {"force_reindex": False}, format="json")
    assert c_resp.status_code == status.HTTP_200_OK
    # Should be skipped since already indexed
    assert c_resp.json()["chunks_skipped"] == data["chunks_indexed"]
