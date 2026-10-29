import pytest
from companies.models import Company
from documents.models import FinancialDocument, DocumentPage, DocumentChunk
from documents.chunking import FinancialDocumentChunker, DocumentIndexingService
from core.embeddings.providers import DeterministicLocalEmbeddingProvider


@pytest.fixture
def sample_company(db):
    return Company.objects.create(
        ticker="RELIANCE",
        slug="reliance",
        name="Reliance Industries Limited",
    )


@pytest.fixture
def sample_document(db, sample_company):
    return FinancialDocument.objects.create(
        company=sample_company,
        external_id="uuid-ril-ar-2026",
        doc_type="annual_report",
        title="Reliance Annual Report 2026",
        fiscal_period="FY26",
    )


@pytest.mark.django_db
def test_chunker_handles_empty_and_whitespace_pages(sample_document):
    """Verify chunker gracefully handles pages that are empty or whitespace only."""
    p1 = DocumentPage.objects.create(
        document=sample_document,
        page_number=1,
        content="   \n\n\t   ",
        content_hash="hash-empty-1",
    )
    p2 = DocumentPage.objects.create(
        document=sample_document,
        page_number=2,
        content="MANAGEMENT DISCUSSION\nReliance Retail continued its aggressive expansion.",
        content_hash="hash-p2",
    )

    chunker = FinancialDocumentChunker(target_chunk_chars=300)
    chunks = chunker.chunk_document_pages([p1, p2])

    # Empty page should not create a blank chunk
    assert len(chunks) == 1
    assert "Reliance Retail" in chunks[0]["content"]
    assert chunks[0]["page_start"] == 2


@pytest.mark.django_db
def test_chunker_handles_non_contiguous_missing_pages(sample_document):
    """Verify chunker handles non-contiguous page gaps (e.g. page 1 then page 45)."""
    p1 = DocumentPage.objects.create(
        document=sample_document,
        page_number=1,
        content="DIRECTORS REPORT\nHighlights of the financial year.",
        content_hash="hash-p1",
    )
    p45 = DocumentPage.objects.create(
        document=sample_document,
        page_number=45,
        content="FINANCIAL HIGHLIGHTS\nJio customer base crossed 480 million subscribers.",
        content_hash="hash-p45",
    )

    chunker = FinancialDocumentChunker(target_chunk_chars=100)
    chunks = chunker.chunk_document_pages([p1, p45])

    assert len(chunks) == 2
    assert chunks[0]["page_start"] == 1
    assert chunks[1]["page_start"] == 45


@pytest.mark.django_db
def test_indexing_service_rejects_document_with_no_pages(sample_document):
    """Verify indexing service raises clear ValueError if document has no pages."""
    provider = DeterministicLocalEmbeddingProvider(dimension=64)
    service = DocumentIndexingService(embedding_provider=provider)

    with pytest.raises(ValueError) as exc_info:
        service.index_document(sample_document)

    assert "has no ingested pages to index" in str(exc_info.value)


@pytest.mark.django_db
def test_chunker_handles_very_large_page_content(sample_document):
    """Verify chunker handles unusually large page text without memory blowout or crash."""
    large_text = ("Jio 5G standalone network deployment accelerated. " * 500)  # ~25,000 chars
    p1 = DocumentPage.objects.create(
        document=sample_document,
        page_number=1,
        content=large_text,
        content_hash="hash-large",
    )

    chunker = FinancialDocumentChunker(target_chunk_chars=1000, overlap_chars=100)
    chunks = chunker.chunk_document_pages([p1])

    assert len(chunks) > 20
    for chunk in chunks:
        assert len(chunk["content"]) > 0
        assert chunk["page_start"] == 1
        assert chunk["page_end"] == 1
