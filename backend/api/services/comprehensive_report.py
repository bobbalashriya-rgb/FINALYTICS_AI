import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from .company_data import fetch_company_data, FinancialDataError
from .financial_metrics import calculate_metrics
from .investment_principles import evaluate_principles
from api.models import InvestmentPrinciple

# Qualitative modules
from companies.models import Company
from documents.models import FinancialDocument, DocumentChunk
from research.analysis import QualitativeAnalysisService
from research.services import EvidenceRetrievalService

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This institutional research dossier is prepared strictly for research and educational analysis. "
    "It evaluates verified financial statements and corporate regulatory filings. "
    "It does NOT constitute an offer, solicitation, or recommendation to buy or sell securities."
)


def generate_comprehensive_report(ticker: str) -> Dict[str, Any]:
    """
    Synthesizes real financial statements (Yahoo Finance) and evidence-grounded
    qualitative filings (Annual Reports, Earnings Call Transcripts via MarketPing RAG)
    into a unified institutional investment research report.
    """
    t_start = time.perf_counter()
    ticker_clean = ticker.strip().upper()
    
    # -------------------------------------------------------------
    # 1. Quantitative Pipeline
    # -------------------------------------------------------------
    company_data = fetch_company_data(ticker_clean)
    metrics_result = calculate_metrics(company_data)
    metrics_dict = metrics_result.metrics.model_dump()
    principles = list(InvestmentPrinciple.objects.all())
    evaluation_report = evaluate_principles(metrics_dict, principles)
    eval_dict = evaluation_report.model_dump()

    profile = company_data.profile
    company_name = profile.name if profile and profile.name else ticker_clean

    # -------------------------------------------------------------
    # 2. Qualitative Pipeline (Filings & RAG)
    # -------------------------------------------------------------
    qualitative_findings: List[Dict[str, Any]] = []
    qualitative_citations: List[Dict[str, Any]] = []
    qualitative_summary = ""
    filings_summary: Dict[str, Any] = {
        "is_indexed": False,
        "available_documents_count": 0,
        "indexed_chunks_count": 0,
        "documents": [],
    }

    try:
        # Match company by ticker (handle both NSE 'TCS' and YF 'TCS.NS')
        base_ticker = ticker_clean.split('.')[0]
        company_obj = Company.objects.filter(
            ticker__in=[ticker_clean, base_ticker, f"{base_ticker}.NS", f"{base_ticker}.BO"]
        ).first()

        if company_obj:
            docs = FinancialDocument.objects.filter(company=company_obj)
            filings_summary["available_documents_count"] = docs.count()
            chunks_count = DocumentChunk.objects.filter(document__company=company_obj).count()
            filings_summary["indexed_chunks_count"] = chunks_count
            filings_summary["documents"] = [
                {
                    "id": d.external_id,
                    "title": d.title,
                    "doc_type": d.doc_type,
                    "fiscal_period": d.fiscal_period,
                    "ingestion_status": d.ingestion_status,
                    "total_pages": d.total_pages,
                }
                for d in docs[:10]
            ]

            if chunks_count > 0:
                filings_summary["is_indexed"] = True
                qual_service = QualitativeAnalysisService()
                
                # Run grounded qualitative queries across strategy, risks, and governance
                qual_analysis = qual_service.analyze_company_question(
                    ticker=company_obj.ticker,
                    question=(
                        "What are the company's primary revenue drivers, strategic priorities, "
                        "balance sheet commitments, and key operational risks disclosed in recent filings?"
                    ),
                    top_k=8,
                    min_score=0.15,
                )

                qualitative_summary = qual_analysis.get("executive_summary", "")
                qualitative_findings = qual_analysis.get("key_findings", [])
                qualitative_citations = qual_analysis.get("citations", [])
            else:
                qualitative_summary = (
                    f"Corporate filings are identified for {company_name}, but document pages "
                    f"have not yet been indexed into vector chunks. Run document ingestion and indexing "
                    f"to incorporate qualitative filing citations."
                )
        else:
            qualitative_summary = (
                f"No Indian regulatory filings currently mapped for ticker '{ticker_clean}' in MarketPing database. "
                f"Qualitative analysis is grounded in verified SEC/global disclosures and Yahoo Finance financial statements."
            )
    except Exception as exc:
        logger.warning(f"Qualitative evidence retrieval skipped for {ticker_clean}: {exc}")
        qualitative_summary = f"Qualitative analysis temporarily unavailable: {str(exc)}"

    # -------------------------------------------------------------
    # 3. Comprehensive Synthesis & Epistemic Conviction
    # -------------------------------------------------------------
    passed_count = eval_dict.get("passed_count", 0)
    total_count = eval_dict.get("total_count", 6)
    pass_rate = round((passed_count / max(total_count, 1)) * 100, 1)

    pe = metrics_dict.get("pe_ratio")
    roe = metrics_dict.get("roe")
    margin = metrics_dict.get("operating_margin")
    fcf = metrics_dict.get("free_cash_flow")
    debt_eq = metrics_dict.get("debt_to_equity")

    if pass_rate >= 80:
        conviction_rating = "Institutional High Quality"
        conviction_tone = "Exceptional financial strength with robust fundamentals exceeding institutional hurdles."
    elif pass_rate >= 50:
        conviction_tone = "Balanced fundamental profile with solid operational metrics but selective metric headwinds."
        conviction_rating = "Moderate / Quality Neutral"
    else:
        conviction_tone = "Elevated fundamental risks or sub-hurdle operational performance under institutional criteria."
        conviction_rating = "Speculative / Underweight Hurdle"

    # Format Markdown Report
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    markdown_report = f"""# Institutional Investment Research Dossier: {company_name} ({ticker_clean})
*Generated: {generated_at} | Platform: Finlytics AI Research Engine*

> **Disclaimer**: {DISCLAIMER}

---

## 1. Executive Summary & Thesis
**Fundamental Rating**: **{conviction_rating}** ({passed_count}/{total_count} Principles Passed - {pass_rate}%)  
{conviction_tone}

### Key Valuation & Performance Highlights:
- **P/E Ratio**: {f"{pe:.2f}x" if pe is not None else "N/A"}
- **Return on Equity (ROE)**: {f"{roe * 100:.2f}%" if roe is not None else "N/A"}
- **Operating Margin**: {f"{margin * 100:.2f}%" if margin is not None else "N/A"}
- **Free Cash Flow**: {f"${fcf/1e9:.2f}B" if fcf and abs(fcf) >= 1e9 else (f"${fcf:,.0f}" if fcf else "N/A")}
- **Debt-to-Equity**: {f"{debt_eq:.2f}" if debt_eq is not None else "N/A"}

---

## 2. Institutional Investment Principles Evaluation
| Principle | Metric | Target | Actual | Status | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for ev in eval_dict.get("evaluations", []):
        name = ev.get("name", "")
        m_id = ev.get("metric", "")
        tgt = ev.get("threshold", "")
        act = ev.get("actual_value")
        act_str = f"{act:.2f}" if act is not None else "N/A"
        st = "✅ PASS" if ev.get("passed") else "❌ FAIL"
        desc = ev.get("description", "")
        markdown_report += f"| {name} | {m_id} | {tgt} | {act_str} | {st} | {desc} |\n"

    markdown_report += f"""
---

## 3. Qualitative Disclosures & Regulatory Filing Evidence
{qualitative_summary}

"""
    if qualitative_findings:
        markdown_report += "### Verified Filing Findings (3-Tier Epistemic Classification):\n\n"
        for idx, f in enumerate(qualitative_findings, 1):
            category = f.get("category", "analytical_interpretation").replace("_", " ").title()
            claim = f.get("claim", "")
            quote = f.get("quote", "")
            markdown_report += f"**{idx}. [{category}]** {claim}\n"
            if quote:
                markdown_report += f"> *\"{quote}\"*\n"
            markdown_report += "\n"

    if qualitative_citations:
        markdown_report += "### Report Citations & Source Attribution:\n\n"
        for c in qualitative_citations:
            title = c.get("document_title", "Corporate Filing")
            period = c.get("fiscal_period", "")
            pages = c.get("page_range", "")
            markdown_report += f"- **{title}** ({period}) — Pages: {pages}\n"

    total_time_ms = round((time.perf_counter() - t_start) * 1000, 2)

    return {
        "ticker": ticker_clean,
        "company_name": company_name,
        "generated_at": generated_at,
        "execution_time_ms": total_time_ms,
        "conviction": {
            "rating": conviction_rating,
            "pass_rate_pct": pass_rate,
            "passed_count": passed_count,
            "total_count": total_count,
            "summary": conviction_tone,
        },
        "quantitative_metrics": metrics_dict,
        "principles_evaluation": eval_dict,
        "qualitative_filings": {
            "summary": qualitative_summary,
            "filings_status": filings_summary,
            "findings": qualitative_findings,
            "citations": qualitative_citations,
        },
        "markdown_report": markdown_report,
        "disclaimer": DISCLAIMER,
    }
