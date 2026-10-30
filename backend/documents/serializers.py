from rest_framework import serializers
from documents.models import FinancialDocument, DocumentPage, DocumentChunk
from companies.serializers import CompanySerializer


class DocumentPageSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieved page content and page metadata.
    """
    class Meta:
        model = DocumentPage
        fields = [
            "id",
            "page_number",
            "char_count",
            "word_count",
            "content_hash",
            "content",
            "created_at",
        ]
        read_only_fields = fields


class DocumentChunkSerializer(serializers.ModelSerializer):
    """
    Serializer for section-aware chunks and embedding metadata.
    """
    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "chunk_index",
            "section_heading",
            "page_start",
            "page_end",
            "char_count",
            "word_count",
            "embedding_model",
            "processing_version",
            "content",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class FinancialDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for normalized financial document metadata.
    """
    class Meta:
        model = FinancialDocument
        fields = [
            "id",
            "external_id",
            "doc_type",
            "title",
            "fiscal_period",
            "period_end_date",
            "filing_date",
            "total_pages",
            "is_navigable",
            "ingestion_status",
            "ingested_pages_count",
            "ingested_at",
            "indexed_chunks_count",
            "last_indexed_at",
            "source_reference",
            "created_at",
        ]
        read_only_fields = fields


class AvailableDocumentsResponseSerializer(serializers.Serializer):
    """
    Response schema for company available documents endpoint.
    """
    company = CompanySerializer()
    total = serializers.IntegerField()
    results = FinancialDocumentSerializer(many=True)


class DocumentIngestRequestSerializer(serializers.Serializer):
    """
    Request payload parameters for document ingestion.
    """
    ingest_all = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If true, ingests all remaining pages of the document up to total_pages",
    )
    page_from = serializers.IntegerField(
        required=False,
        default=None,
        allow_null=True,
        min_value=1,
        help_text="Starting page to ingest (defaults to next un-ingested page, or 1)",
    )
    page_to = serializers.IntegerField(
        required=False,
        default=None,
        min_value=1,
        allow_null=True,
        help_text="Ending page to ingest (optional)",
    )
    max_pages = serializers.IntegerField(
        required=False,
        default=24,
        min_value=1,
        max_value=1000,
        help_text="Maximum batch of pages to retrieve in this run (default: 24, up to 1000)",
    )


class DocumentIngestResponseSerializer(serializers.Serializer):
    """
    Response schema for document ingestion operation.
    """
    document_id = serializers.IntegerField()
    external_id = serializers.CharField()
    title = serializers.CharField()
    status = serializers.ChoiceField(choices=["partial", "completed", "failed", "in_progress"])
    is_full_ingestion = serializers.BooleanField()
    pages_ingested_in_request = serializers.IntegerField()
    total_ingested_pages = serializers.IntegerField()
    total_document_pages = serializers.IntegerField()
    page_range = serializers.DictField()
    ingested_at = serializers.DateTimeField(allow_null=True)


class DocumentIndexRequestSerializer(serializers.Serializer):
    """
    Request parameters for chunking and indexing a document.
    """
    force_reindex = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Force regeneration of embeddings and chunks even if unchanged",
    )
    target_chunk_chars = serializers.IntegerField(
        required=False,
        default=1000,
        min_value=200,
        max_value=5000,
        help_text="Target character count per chunk (default: 1000)",
    )
    overlap_chars = serializers.IntegerField(
        required=False,
        default=150,
        min_value=0,
        max_value=500,
        help_text="Character overlap between consecutive chunks (default: 150)",
    )


class DocumentIndexResponseSerializer(serializers.Serializer):
    """
    Response schema for document chunking and indexing.
    """
    document_id = serializers.IntegerField()
    external_id = serializers.CharField()
    title = serializers.CharField()
    chunks_processed = serializers.IntegerField()
    chunks_indexed = serializers.IntegerField()
    chunks_skipped = serializers.IntegerField()
    total_chunks_stored = serializers.IntegerField()
    embedding_model = serializers.CharField()
    embedding_dimension = serializers.IntegerField()
    processing_version = serializers.CharField()
    indexed_at = serializers.DateTimeField(allow_null=True)
