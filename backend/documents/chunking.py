import hashlib
import logging
import re
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from documents.models import FinancialDocument, DocumentPage, DocumentChunk
from core.embeddings import get_embedding_provider

logger = logging.getLogger(__name__)

# Common financial report section patterns for Indian corporate filings
HEADING_PATTERNS = [
    re.compile(r"^(?:management\s+discussion\s+and\s+analysis|md&a)", re.IGNORECASE),
    re.compile(r"^(?:directors'?\s+report|board'?s\s+report)", re.IGNORECASE),
    re.compile(r"^(?:independent\s+auditors?'?\s+report|auditors?'?\s+report)", re.IGNORECASE),
    re.compile(r"^(?:balance\s+sheet|statement\s+of\s+assets\s+and\s+liabilities)", re.IGNORECASE),
    re.compile(r"^(?:statement\s+of\s+profit\s+and\s+loss|income\s+statement)", re.IGNORECASE),
    re.compile(r"^(?:cash\s+flow\s+statement)", re.IGNORECASE),
    re.compile(r"^(?:notes\s+to\s+(?:the\s+)?financial\s+statements)", re.IGNORECASE),
    re.compile(r"^(?:business\s+overview|company\s+overview)", re.IGNORECASE),
    re.compile(r"^(?:operational\s+highlights|financial\s+highlights)", re.IGNORECASE),
    re.compile(r"^(?:corporate\s+governance\s+report)", re.IGNORECASE),
    re.compile(r"^(?:business\s+responsibility\s+and\s+sustainability\s+report|brsr)", re.IGNORECASE),
    re.compile(r"^(?:question[\s\-]+and[\s\-]+answer\s+session|q&a\s+session|participants|executives)", re.IGNORECASE),
    re.compile(r"^(?:safe\s+harbor\s+statement|disclaimer)", re.IGNORECASE),
]


def detect_heading(line: str) -> Optional[str]:
    """Detects whether a line represents a financial section heading."""
    clean = line.strip()
    if not clean or len(clean) > 100:
        return None

    # Markdown header
    if clean.startswith("#"):
        return clean.lstrip("#").strip()

    # Pattern match
    for pattern in HEADING_PATTERNS:
        if pattern.search(clean):
            return clean

    # All-caps title (at least 3 words, under 80 chars)
    if clean.isupper() and 2 <= len(clean.split()) <= 10:
        return clean

    return None


class FinancialDocumentChunker:
    """
    Section-aware, page-attributed chunking for financial reports and transcripts.
    Preserves table structure, heading hierarchy, and source page ranges.
    """

    def __init__(
        self,
        target_chunk_chars: int = 1000,
        overlap_chars: int = 150,
        processing_version: str = "v1.0",
    ):
        self.target_chunk_chars = target_chunk_chars
        self.overlap_chars = overlap_chars
        self.processing_version = processing_version

    def chunk_document_pages(
        self, pages: List[DocumentPage]
    ) -> List[Dict[str, Any]]:
        """
        Splits stored document pages into section-aware, page-attributed chunks.
        Gracefully handles empty pages, non-contiguous gaps, and giant unformatted lines.
        """
        if not pages:
            return []

        chunks: List[Dict[str, Any]] = []
        current_heading = "General Overview"
        current_text_parts: List[str] = []
        current_char_count = 0
        current_start_page: Optional[int] = None
        current_end_page: Optional[int] = None
        chunk_idx = 0

        for page in pages:
            page_text = page.content or ""
            if not page_text.strip():
                continue

            page_num = page.page_number
            raw_lines = page_text.splitlines()

            # Flatten long lines into reasonable segments if any line exceeds target_chunk_chars
            lines: List[str] = []
            for rline in raw_lines:
                clean_rline = rline.strip()
                if not clean_rline:
                    continue
                if len(clean_rline) > self.target_chunk_chars:
                    # Break long line by sentences or fixed chunks
                    step = max(100, self.target_chunk_chars - self.overlap_chars)
                    for start_i in range(0, len(clean_rline), step):
                        lines.append(clean_rline[start_i : start_i + step])
                else:
                    lines.append(clean_rline)

            for line in lines:
                h = detect_heading(line)
                if h:
                    current_heading = h

                line_len = len(line) + 1  # include newline

                # If adding line exceeds target and we already have substantive content
                if current_char_count + line_len > self.target_chunk_chars and current_text_parts:
                    chunk_text = "\n".join(current_text_parts).strip()
                    if chunk_text:
                        chunks.append(
                            {
                                "chunk_index": chunk_idx,
                                "content": chunk_text,
                                "section_heading": current_heading,
                                "page_start": current_start_page if current_start_page is not None else page_num,
                                "page_end": current_end_page if current_end_page is not None else page_num,
                                "char_count": len(chunk_text),
                                "word_count": len(chunk_text.split()),
                            }
                        )
                        chunk_idx += 1

                    # Retain overlap from end of current chunk
                    overlap_parts: List[str] = []
                    overlap_len = 0
                    for part in reversed(current_text_parts):
                        if overlap_len + len(part) <= self.overlap_chars:
                            overlap_parts.insert(0, part)
                            overlap_len += len(part)
                        else:
                            break

                    current_text_parts = overlap_parts
                    current_char_count = overlap_len
                    current_start_page = page_num

                if not current_text_parts:
                    current_start_page = page_num

                current_text_parts.append(line)
                current_char_count += line_len
                current_end_page = page_num

        # Flush final remaining chunk
        if current_text_parts:
            final_text = "\n".join(current_text_parts).strip()
            if final_text:
                chunks.append(
                    {
                        "chunk_index": chunk_idx,
                        "content": final_text,
                        "section_heading": current_heading,
                        "page_start": current_start_page if current_start_page is not None else pages[-1].page_number,
                        "page_end": current_end_page if current_end_page is not None else pages[-1].page_number,
                        "char_count": len(final_text),
                        "word_count": len(final_text.split()),
                    }
                )

        return chunks


class DocumentIndexingService:
    """
    Orchestrates section-aware chunking, vector embedding generation,
    and idempotent storage into PostgreSQL.
    """

    def __init__(
        self,
        chunker: Optional[FinancialDocumentChunker] = None,
        embedding_provider=None,
    ):
        self.chunker = chunker or FinancialDocumentChunker()
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def index_document(
        self,
        document: FinancialDocument,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Chunks all stored pages of a document, computes vector embeddings,
        and saves chunks into PostgreSQL idempotently.
        """
        pages = list(document.pages.order_by("page_number"))
        if not pages:
            raise ValueError(
                f"Document '{document.id}' ({document.title}) has no ingested pages to index. Ingest pages first."
            )

        # 1. Chunk document pages
        raw_chunks = self.chunker.chunk_document_pages(pages)
        if not raw_chunks:
            raise ValueError("No text content could be extracted into chunks.")

        model_name = self.embedding_provider.model_name
        version = self.chunker.processing_version

        # 2. Check existing chunks for idempotency
        existing_chunks = {
            c.chunk_index: c
            for c in DocumentChunk.objects.filter(
                document=document, processing_version=version
            )
        }

        chunks_to_embed: List[Dict[str, Any]] = []
        chunks_to_skip: int = 0
        chunks_to_update: List[Dict[str, Any]] = []

        for item in raw_chunks:
            c_idx = item["chunk_index"]
            c_text = item["content"]
            c_hash = hashlib.sha256(
                f"{document.id}:{c_idx}:{c_text}".encode("utf-8")
            ).hexdigest()
            item["chunk_hash"] = c_hash

            existing = existing_chunks.get(c_idx)
            if (
                not force_reindex
                and existing
                and existing.chunk_hash == c_hash
                and existing.embedding_model == model_name
                and existing.embedding
            ):
                chunks_to_skip += 1
            else:
                chunks_to_embed.append(item)

        # 3. Generate embeddings for new/modified chunks in batches
        indexed_count = 0
        if chunks_to_embed:
            logger.info(
                "Generating embeddings for %d chunks of document %s using %s",
                len(chunks_to_embed),
                document.external_id,
                model_name,
            )
            texts = [c["content"] for c in chunks_to_embed]
            try:
                embeddings = self.embedding_provider.embed_texts(texts)
            except Exception as exc:
                logger.exception("Embedding generation failed: %s", exc)
                raise RuntimeError(
                    f"Embedding provider '{model_name}' failed to generate embeddings: {exc}"
                ) from exc

            # 4. Save chunks and embeddings to PostgreSQL
            with transaction.atomic():
                for chunk_data, emb in zip(chunks_to_embed, embeddings):
                    metadata = {
                        "company_ticker": document.company.ticker,
                        "company_name": document.company.name,
                        "doc_type": document.doc_type,
                        "fiscal_period": document.fiscal_period,
                        "period_end_date": str(document.period_end_date)
                        if document.period_end_date
                        else None,
                        "source_reference": document.source_reference,
                    }

                    DocumentChunk.objects.update_or_create(
                        document=document,
                        chunk_index=chunk_data["chunk_index"],
                        processing_version=version,
                        defaults={
                            "content": chunk_data["content"],
                            "chunk_hash": chunk_data["chunk_hash"],
                            "section_heading": chunk_data["section_heading"],
                            "page_start": chunk_data["page_start"],
                            "page_end": chunk_data["page_end"],
                            "char_count": chunk_data["char_count"],
                            "word_count": chunk_data["word_count"],
                            "embedding_model": model_name,
                            "embedding": emb,
                            "metadata": metadata,
                        },
                    )
                    indexed_count += 1

        # 5. Update document indexing status
        total_chunks = DocumentChunk.objects.filter(
            document=document, processing_version=version
        ).count()
        document.indexed_chunks_count = total_chunks
        document.last_indexed_at = timezone.now()
        document.save(update_fields=["indexed_chunks_count", "last_indexed_at", "updated_at"])

        return {
            "document_id": document.id,
            "external_id": document.external_id,
            "title": document.title,
            "chunks_processed": len(raw_chunks),
            "chunks_indexed": indexed_count,
            "chunks_skipped": chunks_to_skip,
            "total_chunks_stored": total_chunks,
            "embedding_model": model_name,
            "embedding_dimension": self.embedding_provider.dimension,
            "processing_version": version,
            "indexed_at": document.last_indexed_at.isoformat()
            if document.last_indexed_at
            else None,
        }
