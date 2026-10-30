import logging
import re
from typing import Any, Dict, List, Set

from research.services import extract_keywords

logger = logging.getLogger(__name__)


class AnalysisEvaluator:
    """
    Evaluates retrieval relevance and answer faithfulness for qualitative financial research RAG.
    Validates citation accuracy, detects unsupported claims, and measures grounding metrics.
    """

    def evaluate(
        self,
        question: str,
        analysis_result: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Computes formal evaluation metrics comparing the generated qualitative analysis
        against the retrieved source evidence passages.
        """
        # 1. Retrieval Metrics
        query_keywords = extract_keywords(question)
        evidence_chunks = retrieved_evidence or []
        evidence_count = len(evidence_chunks)

        if evidence_count > 0:
            relevance_scores = [c.get("relevance_score", 0.0) for c in evidence_chunks]
            mean_relevance = round(sum(relevance_scores) / evidence_count, 4)
            top_relevance = round(max(relevance_scores), 4)

            # Keyword coverage
            all_evidence_text = " ".join(c.get("content", "") for c in evidence_chunks).lower()
            covered_keywords = {kw for kw in query_keywords if kw in all_evidence_text}
            keyword_coverage = (
                round(len(covered_keywords) / len(query_keywords), 4)
                if query_keywords
                else 1.0
            )

            distinct_docs = len({c.get("document_id") for c in evidence_chunks if c.get("document_id")})
        else:
            mean_relevance = 0.0
            top_relevance = 0.0
            keyword_coverage = 0.0
            distinct_docs = 0

        retrieval_metrics = {
            "retrieval_hit_rate": 1.0 if evidence_count > 0 else 0.0,
            "evidence_chunks_count": evidence_count,
            "mean_relevance_score": mean_relevance,
            "top_relevance_score": top_relevance,
            "keyword_coverage_ratio": keyword_coverage,
            "distinct_source_documents": distinct_docs,
        }

        # 2. Faithfulness & Citation Accuracy Metrics
        valid_chunk_ids: Set[int] = {c.get("chunk_id") for c in evidence_chunks if c.get("chunk_id") is not None}
        key_findings = analysis_result.get("key_findings", [])
        total_claims = len(key_findings)

        supported_claims = 0
        unsupported_claims = 0
        all_cited_chunk_ids: List[int] = []
        epistemic_counts = {
            "reported_fact": 0,
            "management_statement": 0,
            "analytical_interpretation": 0,
        }

        for finding in key_findings:
            category = finding.get("category", "analytical_interpretation")
            epistemic_counts[category] = epistemic_counts.get(category, 0) + 1

            chunk_ids = finding.get("chunk_ids", [])
            all_cited_chunk_ids.extend(chunk_ids)

            # Claim is supported if it has at least one chunk ID belonging to valid retrieved chunks
            valid_supporting_cids = [cid for cid in chunk_ids if cid in valid_chunk_ids]
            if valid_supporting_cids:
                supported_claims += 1
            else:
                unsupported_claims += 1

        total_citations = len(all_cited_chunk_ids)
        if total_citations > 0:
            verified_citations = sum(1 for cid in all_cited_chunk_ids if cid in valid_chunk_ids)
            citation_verification_rate = round(verified_citations / total_citations, 4)
            hallucinated_citations_count = total_citations - verified_citations
        else:
            citation_verification_rate = 1.0 if total_claims == 0 else 0.0
            hallucinated_citations_count = 0

        supported_claims_ratio = (
            round(supported_claims / total_claims, 4) if total_claims > 0 else 0.0
        )

        missing_info = analysis_result.get("missing_information_and_limitations", [])
        limitations_disclosed = len(missing_info) > 0

        faithfulness_metrics = {
            "total_claims_evaluated": total_claims,
            "supported_claims_count": supported_claims,
            "unsupported_claims_count": unsupported_claims,
            "supported_claims_ratio": supported_claims_ratio,
            "citation_verification_rate": citation_verification_rate,
            "hallucinated_citations_count": hallucinated_citations_count,
            "has_hallucinated_citations": hallucinated_citations_count > 0,
            "epistemic_distribution": epistemic_counts,
            "limitations_disclosed": limitations_disclosed,
        }

        # 3. Overall Composite Quality Score (0.0 to 1.0)
        # Weighted formula:
        # 40% citation accuracy + 30% supported claims + 20% relevance + 10% limitations disclosure
        limitation_bonus = 1.0 if limitations_disclosed else 0.5
        overall_score = round(
            0.40 * citation_verification_rate
            + 0.30 * supported_claims_ratio
            + 0.20 * min(1.0, mean_relevance * 1.5)  # Scale up normalized relevance
            + 0.10 * limitation_bonus,
            4,
        )

        logger.info(
            "Evaluation complete: Faithfulness Score: %.2f | Citation Accuracy: %.2f | Supported Claims: %d/%d",
            overall_score,
            citation_verification_rate,
            supported_claims,
            total_claims,
        )

        return {
            "overall_quality_score": overall_score,
            "retrieval_metrics": retrieval_metrics,
            "faithfulness_metrics": faithfulness_metrics,
        }
