import logging
import math
import re
from typing import Any, Dict, List, Optional, Set

from companies.models import Company
from companies.services import CompanyService
from companies.exceptions import CompanyNotFoundError
from documents.models import FinancialDocument, DocumentChunk
from core.embeddings import get_embedding_provider

logger = logging.getLogger(__name__)


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine similarity between two float vectors.
    Returns a float in range [-1.0, 1.0].
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def extract_keywords(text: str) -> Set[str]:
    """
    Extracts significant lowercase keywords (words with length >= 3)
    excluding common english stopwords.
    """
    STOPWORDS = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was",
        "were", "will", "would", "what", "which", "when", "where", "how",
        "has", "had", "have", "been", "about", "into", "their", "them",
        "than", "its", "also", "some", "most", "over", "such", "our",
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


class EvidenceRetrievalService:
    """
    Retrieves and ranks relevant report passages for qualitative research questions.
    Combines dense semantic vector retrieval with keyword relevance (hybrid search),
    enforces company isolation, and supports document type and fiscal period filtering.
    """

    def __init__(self, embedding_provider=None):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.company_service = CompanyService()

    def retrieve_evidence(
        self,
        ticker: str,
        question: str,
        document_types: Optional[List[str]] = None,
        fiscal_periods: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Executes evidence retrieval for a given company and research question.
        """
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Research question cannot be empty.")

        # 1. Resolve company
        company = self.company_service.get_or_resolve_company(query=ticker)

        # 2. Query available indexed chunks for this company only
        chunks_qs = DocumentChunk.objects.filter(document__company=company).select_related("document")

        if document_types:
            clean_types = [dt.strip().lower() for dt in document_types if dt.strip()]
            if clean_types:
                chunks_qs = chunks_qs.filter(document__doc_type__in=clean_types)

        if fiscal_periods:
            clean_periods = [fp.strip().upper() for fp in fiscal_periods if fp.strip()]
            if clean_periods:
                chunks_qs = chunks_qs.filter(document__fiscal_period__in=clean_periods)

        total_chunks = chunks_qs.count()
        if total_chunks == 0:
            return {
                "ticker": company.ticker,
                "company_name": company.name,
                "question": clean_question,
                "total_chunks_searched": 0,
                "total_evidence_found": 0,
                "has_evidence": false if False else False,
                "message": (
                    f"No indexed document chunks found for company '{company.ticker}'. "
                    f"Please verify that documents have been ingested and indexed."
                ),
                "evidence": [],
            }

        # 3. Generate embedding for query
        query_embeddings = self.embedding_provider.embed_texts([clean_question])
        if not query_embeddings or not query_embeddings[0]:
            raise RuntimeError("Failed to compute embedding for the research question.")
        query_vector = query_embeddings[0]

        query_keywords = extract_keywords(clean_question)

        # 4. Score each candidate chunk
        scored_candidates: List[Dict[str, Any]] = []

        for chunk in chunks_qs:
            chunk_embedding = chunk.embedding
            if not chunk_embedding:
                continue

            # Dense semantic similarity
            semantic_score = compute_cosine_similarity(query_vector, chunk_embedding)
            # Normalize cosine score from [-1, 1] to [0, 1]
            normalized_semantic = max(0.0, (semantic_score + 1.0) / 2.0)

            # Lexical / keyword overlap
            chunk_keywords = extract_keywords(chunk.content + " " + (chunk.section_heading or ""))
            matched_keywords = sorted(list(query_keywords.intersection(chunk_keywords)))
            keyword_ratio = (
                len(matched_keywords) / len(query_keywords)
                if query_keywords
                else 0.0
            )

            # Hybrid score: 75% semantic weight + 25% lexical keyword overlap
            hybrid_score = round(0.75 * normalized_semantic + 0.25 * keyword_ratio, 4)

            if hybrid_score >= min_score:
                scored_candidates.append(
                    {
                        "chunk_id": chunk.id,
                        "chunk_index": chunk.chunk_index,
                        "document_id": chunk.document.id,
                        "document_external_id": chunk.document.external_id,
                        "document_title": chunk.document.title,
                        "document_type": chunk.document.doc_type,
                        "fiscal_period": chunk.document.fiscal_period,
                        "period_end_date": str(chunk.document.period_end_date)
                        if chunk.document.period_end_date
                        else None,
                        "section_heading": chunk.section_heading or "General Content",
                        "page_start": chunk.page_start,
                        "page_end": chunk.page_end,
                        "content": chunk.content,
                        "relevance_score": hybrid_score,
                        "semantic_similarity": round(normalized_semantic, 4),
                        "keyword_matches": matched_keywords,
                        "source_reference": chunk.document.source_reference,
                    }
                )

        # 5. Sort by relevance descending
        scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        # 6. Deduplicate adjacent/overlapping chunks from the same document
        deduplicated: List[Dict[str, Any]] = []
        seen_keys = set()

        for cand in scored_candidates:
            # Group key by document and page range to avoid redundant identical paragraphs
            key = (cand["document_id"], cand["page_start"], cand["section_heading"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduplicated.append(cand)
            if len(deduplicated) >= top_k:
                break

        has_evidence = len(deduplicated) > 0
        message = (
            f"Successfully retrieved {len(deduplicated)} relevant evidence passages."
            if has_evidence
            else "No report passages met the minimum relevance threshold for this query."
        )

        return {
            "ticker": company.ticker,
            "company_name": company.name,
            "question": clean_question,
            "total_chunks_searched": total_chunks,
            "total_evidence_found": len(deduplicated),
            "has_evidence": has_evidence,
            "message": message,
            "evidence": deduplicated,
        }
