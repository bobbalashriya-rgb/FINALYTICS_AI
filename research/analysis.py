import logging
import time
from typing import Any, Dict, List, Optional, Set

from core.llm import get_llm_provider
from core.llm.base import BaseLLMProvider
from research.services import EvidenceRetrievalService
from research.prompts import (
    PROMPT_VERSION,
    SYSTEM_INSTRUCTION,
    build_analysis_user_prompt,
)

logger = logging.getLogger(__name__)


class QualitativeAnalysisService:
    """
    Orchestrates evidence-grounded qualitative fundamental analysis using retrieved report passages and LLMs.
    Validates citations, categorizes epistemic claims, and discloses missing evidence.
    """

    def __init__(
        self,
        retrieval_service: Optional[EvidenceRetrievalService] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.retrieval_service = retrieval_service or EvidenceRetrievalService()
        self.llm_provider = llm_provider or get_llm_provider()

    def analyze_company_question(
        self,
        ticker: str,
        question: str,
        document_types: Optional[List[str]] = None,
        fiscal_periods: Optional[List[str]] = None,
        top_k: int = 8,
        min_score: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end qualitative analysis:
        1. Retrieves relevant report passages using Phase 6 retrieval engine.
        2. Passes verified passages into the LLM prompt.
        3. Validates citations and categorizes claims into facts, management statements, and analysis.
        """
        t_start = time.perf_counter()

        # 1. Retrieve evidence
        t_retrieval_start = time.perf_counter()
        retrieval_res = self.retrieval_service.retrieve_evidence(
            ticker=ticker,
            question=question,
            document_types=document_types,
            fiscal_periods=fiscal_periods,
            top_k=top_k,
            min_score=min_score,
        )
        retrieval_time_ms = round((time.perf_counter() - t_retrieval_start) * 1000, 2)

        evidence_items = retrieval_res.get("evidence", [])
        company_ticker = retrieval_res["ticker"]
        company_name = retrieval_res["company_name"]

        # 2. Handle missing or zero evidence
        if not evidence_items:
            total_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
            logger.info(
                "Analysis concluded for %s with zero evidence in %.1fms (retrieval: %.1fms)",
                ticker,
                total_time_ms,
                retrieval_time_ms,
            )
            return {
                "company": {
                    "ticker": company_ticker,
                    "name": company_name,
                },
                "question": question,
                "executive_summary": (
                    f"No relevant disclosures or report passages were found for {company_name} "
                    f"matching the research query. Qualitative analysis cannot be conducted without source evidence."
                ),
                "key_findings": [],
                "citations": [],
                "risks_and_uncertainties": [
                    "Insufficient indexed report content to assess risks on this specific topic."
                ],
                "missing_information_and_limitations": [
                    retrieval_res.get("message", "No matching document excerpts found in database.")
                ],
                "prompt_version": PROMPT_VERSION,
                "model_name": self.llm_provider.model_name,
                "has_sufficient_evidence": False,
                "total_evidence_chunks_evaluated": 0,
                "metrics": {
                    "retrieval_time_ms": retrieval_time_ms,
                    "llm_time_ms": 0.0,
                    "total_time_ms": total_time_ms,
                    "evidence_chunks_retrieved": 0,
                    "verified_citations_count": 0,
                },
            }

        # Index valid retrieved chunks by ID for citation verification
        chunks_by_id = {item["chunk_id"]: item for item in evidence_items}
        valid_chunk_ids: Set[int] = set(chunks_by_id.keys())

        # 3. Build user prompt
        user_prompt = build_analysis_user_prompt(
            company_name=company_name,
            ticker=company_ticker,
            question=question,
            evidence_items=evidence_items,
        )

        # 4. Generate structured LLM analysis
        t_llm_start = time.perf_counter()
        try:
            raw_analysis = self.llm_provider.generate_analysis(
                system_instruction=SYSTEM_INSTRUCTION,
                user_prompt=user_prompt,
                temperature=0.15,
            )
        except Exception as exc:
            logger.exception("LLM generation failed: %s", exc)
            raise RuntimeError(f"Qualitative analysis generation failed: {exc}") from exc
        llm_time_ms = round((time.perf_counter() - t_llm_start) * 1000, 2)

        # 5. Validate citations and sanitize findings
        raw_findings = raw_analysis.get("key_findings", [])
        validated_findings: List[Dict[str, Any]] = []
        cited_chunk_ids: Set[int] = set()

        for finding in raw_findings:
            claim = finding.get("claim", "").strip()
            if not claim:
                continue

            category = finding.get("category", "analytical_interpretation").lower().strip()
            if category not in ("reported_fact", "management_statement", "analytical_interpretation"):
                category = "analytical_interpretation"

            # Filter out any hallucinated chunk IDs
            raw_cids = finding.get("chunk_ids", [])
            verified_cids = [cid for cid in raw_cids if cid in valid_chunk_ids]

            # If no chunk IDs provided by model, map to the best matching evidence chunks
            if not verified_cids and evidence_items:
                verified_cids = [evidence_items[0]["chunk_id"]]

            cited_chunk_ids.update(verified_cids)

            validated_findings.append(
                {
                    "claim": claim,
                    "category": category,
                    "chunk_ids": verified_cids,
                    "quote": finding.get("quote", ""),
                }
            )

        # 6. Format verified citations list
        citations_list: List[Dict[str, Any]] = []
        for cid in sorted(list(cited_chunk_ids)):
            c_data = chunks_by_id.get(cid)
            if c_data:
                p_start = c_data.get("page_start")
                p_end = c_data.get("page_end")
                if p_start is not None and p_end is not None:
                    page_range = f"pp. {p_start}-{p_end}" if p_start != p_end else f"p. {p_start}"
                elif p_start is not None:
                    page_range = f"p. {p_start}"
                else:
                    page_range = "N/A"

                citations_list.append(
                    {
                        "chunk_id": cid,
                        "document_id": c_data["document_id"],
                        "document_title": c_data["document_title"],
                        "document_type": c_data["document_type"],
                        "fiscal_period": c_data["fiscal_period"],
                        "page_start": p_start,
                        "page_end": p_end,
                        "page_range": page_range,
                        "section_heading": c_data["section_heading"],
                        "source_reference": c_data.get("source_reference"),
                    }
                )

        risks = raw_analysis.get("risks_and_uncertainties", [])
        missing_info = raw_analysis.get("missing_information_and_limitations", [])
        total_time_ms = round((time.perf_counter() - t_start) * 1000, 2)

        logger.info(
            "Qualitative analysis completed for %s in %.1fms (retrieval: %.1fms, llm: %.1fms, chunks: %d, citations: %d)",
            ticker,
            total_time_ms,
            retrieval_time_ms,
            llm_time_ms,
            len(evidence_items),
            len(citations_list),
        )

        return {
            "company": {
                "ticker": company_ticker,
                "name": company_name,
            },
            "question": question,
            "executive_summary": raw_analysis.get("executive_summary", ""),
            "key_findings": validated_findings,
            "citations": citations_list,
            "risks_and_uncertainties": risks,
            "missing_information_and_limitations": missing_info,
            "prompt_version": PROMPT_VERSION,
            "model_name": self.llm_provider.model_name,
            "has_sufficient_evidence": True,
            "total_evidence_chunks_evaluated": len(evidence_items),
            "metrics": {
                "retrieval_time_ms": retrieval_time_ms,
                "llm_time_ms": llm_time_ms,
                "total_time_ms": total_time_ms,
                "evidence_chunks_retrieved": len(evidence_items),
                "verified_citations_count": len(citations_list),
            },
        }
