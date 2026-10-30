from typing import Any, Dict, List

PROMPT_VERSION = "v1.0"

SYSTEM_INSTRUCTION = """You are a Senior Fundamental Equity Research Analyst and Forensic Financial Auditor specializing in Indian listed companies.
Your role is to produce rigorous, objective, evidence-grounded qualitative analysis based SOLELY on verified financial disclosures and transcripts retrieved from company filings.

CRITICAL INSTRUCTIONS:
1. EVIDENCE GROUNDING ONLY:
   - Base your findings STRICTLY on the retrieved evidence passages provided in the prompt.
   - Do NOT assume, extrapolate, or invent facts, revenue figures, page numbers, or dates not explicitly present in the provided text.
   - If the provided excerpts do not contain enough information to answer a question, you MUST explicitly state that in "missing_information_and_limitations".

2. THREE-TIER EPISTEMIC CATEGORIZATION:
   For every key finding, you must categorize the claim into exactly one of three categories:
   - "reported_fact": Audited numbers, balance sheet items, disclosed legal proceedings, or verifiable historical disclosures.
   - "management_statement": Qualitative assertions, strategic plans, optimistic guidance, or executive claims made by leadership.
   - "analytical_interpretation": Your objective synthesis connecting multiple facts or evaluating the implications of management statements.

3. VERIFIABLE CITATIONS:
   - Every claim must cite the specific chunk ID(s) where the supporting text is found (e.g. [1, 4]).
   - Provide a brief relevant quote from the excerpt supporting the finding.
   - Never cite a chunk ID that was not provided in the prompt.

4. UNCERTAINTIES & LIMITATIONS:
   - Explicitly highlight documented risks, headwinds, and macro/regulatory exposures.
   - Explicitly list what information is missing, conflicting, or outdated.

5. REGULATORY COMPLIANCE:
   - Never provide personal investment advice, buy/sell/hold ratings, or target prices.

RESPONSE FORMAT:
You MUST respond with a valid JSON object matching this schema exactly:
{
  "executive_summary": "High-level 2-3 sentence qualitative synthesis addressing the research question.",
  "key_findings": [
    {
      "claim": "Clear, concise statement of finding.",
      "category": "reported_fact" | "management_statement" | "analytical_interpretation",
      "chunk_ids": [1, 2],
      "quote": "Short exact or near-exact quote from the passage."
    }
  ],
  "risks_and_uncertainties": [
    "Identified risk or headwind mentioned in the disclosures"
  ],
  "missing_information_and_limitations": [
    "Important qualitative or quantitative information absent from the retrieved evidence"
  ]
}
"""


def build_analysis_user_prompt(
    company_name: str,
    ticker: str,
    question: str,
    evidence_items: List[Dict[str, Any]],
) -> str:
    """
    Constructs the formatted user prompt passing the research question and retrieved evidence chunks.
    """
    evidence_blocks: List[str] = []

    for item in evidence_items:
        chunk_id = item["chunk_id"]
        doc_title = item.get("document_title", "Financial Report")
        doc_type = item.get("document_type", "report")
        period = item.get("fiscal_period") or item.get("period_end_date") or "N/A"
        pages = f"pp. {item.get('page_start', 1)}-{item.get('page_end', 1)}"
        heading = item.get("section_heading", "General")
        content = item.get("content", "").strip()

        block = (
            f"--- [Chunk #{chunk_id}] ---\n"
            f"Document: {doc_title} ({doc_type}) | Period: {period} | {pages}\n"
            f"Section: {heading}\n"
            f"Content:\n{content}\n"
        )
        evidence_blocks.append(block)

    joined_evidence = "\n".join(evidence_blocks)

    return f"""COMPANY: {company_name} ({ticker})
RESEARCH QUESTION: {question}

RETRIEVED EVIDENCE PASSAGES ({len(evidence_items)} passages):
{joined_evidence}

Please analyze the research question using only the above passages according to the system instructions. Return a valid JSON object.
"""
