from django.db import models
from companies.models import Company


class FinancialDocument(models.Model):
    """
    Persistent model representing a financial document (Annual Report, Earnings Call Transcript, etc.)
    discovered via MarketPing MCP.
    """
    DOCUMENT_TYPES = [
        ("annual_report", "Annual Report"),
        ("earnings_call_transcript", "Earnings Call Transcript"),
        ("financial_results", "Financial Results"),
        ("investor_presentation", "Investor Presentation"),
        ("announcement", "Announcement"),
        ("brsr", "BRSR"),
        ("other", "Other"),
    ]

    INGESTION_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("partial", "Partially Ingested"),
        ("completed", "Fully Ingested"),
        ("failed", "Failed"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    external_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique MarketPing document UUID",
    )
    doc_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    fiscal_period = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g. FY27 Q2 or FY26",
    )
    period_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Reporting period end date (e.g. 2026-06-30)",
    )
    filing_date = models.DateField(
        null=True,
        blank=True,
        help_text="Document filing date (e.g. 2026-07-28)",
    )
    total_pages = models.PositiveIntegerField(default=1)
    is_navigable = models.BooleanField(default=True)
    source_reference = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Source reference or MarketPing canonical URL",
    )

    # Ingestion tracking
    ingestion_status = models.CharField(
        max_length=20,
        choices=INGESTION_STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    ingested_pages_count = models.PositiveIntegerField(default=0)
    ingested_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, null=True)

    # Indexing / Embedding tracking
    indexed_chunks_count = models.PositiveIntegerField(default=0)
    last_indexed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_end_date", "-filing_date", "-created_at"]
        verbose_name_plural = "Financial Documents"

    def __str__(self):
        return f"{self.company.ticker} - {self.title} ({self.fiscal_period or self.period_end_date or 'N/A'})"


class DocumentPage(models.Model):
    """
    Extracted page text and metadata retrieved from MarketPing MCP read_pages.
    Preserves exact page numbering, source traceability, and tabular alignment.
    """
    document = models.ForeignKey(
        FinancialDocument,
        on_delete=models.CASCADE,
        related_name="pages",
    )
    page_number = models.PositiveIntegerField(help_text="1-based page number")
    content = models.TextField(help_text="Extracted page text")
    content_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of normalized content for idempotency checks",
    )
    char_count = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["document", "page_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "page_number"],
                name="unique_document_page",
            )
        ]
        verbose_name_plural = "Document Pages"

    def __str__(self):
        return f"{self.document.title} - Page {self.page_number}"


class DocumentChunk(models.Model):
    """
    Section-aware, semantically cohesive chunk extracted from document pages
    with vector embedding and traceable source metadata.
    """
    document = models.ForeignKey(
        FinancialDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField(db_index=True)
    content = models.TextField(help_text="Text content of the chunk")
    chunk_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of the chunk text",
    )
    section_heading = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Nearest detected heading or section name",
    )
    page_start = models.PositiveIntegerField(help_text="First page containing this chunk content")
    page_end = models.PositiveIntegerField(help_text="Last page containing this chunk content")
    char_count = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0)

    # Embedding and processing metadata
    embedding_model = models.CharField(max_length=100, db_index=True)
    processing_version = models.CharField(max_length=50, default="v1.0", db_index=True)
    embedding = models.JSONField(
        default=list,
        help_text="Vector embedding representation (float list)",
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Traceable source identifiers, company, fiscal period, doc type",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index", "processing_version"],
                name="unique_document_chunk_version",
            )
        ]
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        return f"{self.document.title} - Chunk #{self.chunk_index} (pp. {self.page_start}-{self.page_end})"
