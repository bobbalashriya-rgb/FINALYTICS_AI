import pytest
from rest_framework import status
from rest_framework.test import APIClient

from companies.models import Company
from companies.services import CompanyService
from companies.exceptions import CompanyNotFoundError
from documents.models import FinancialDocument, DocumentChunk
from core.embeddings.providers import DeterministicLocalEmbeddingProvider
from core.llm.providers import MockLLMProvider
from research.services import EvidenceRetrievalService
from research.analysis import QualitativeAnalysisService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_data(db):
    provider = DeterministicLocalEmbeddingProvider(dimension=128)

    # 1. Company 1: INFY
    infy = Company.objects.create(ticker="INFY", slug="infosys", name="Infosys Limited")
    infy_ar = FinancialDocument.objects.create(
        company=infy,
        external_id="uuid-infy-ar-fy26",
        doc_type="annual_report",
        title="Infosys Annual Report 2026",
        fiscal_period="FY26",
        period_end_date="2026-03-31",
        total_pages=360,
    )
    infy_transcript = FinancialDocument.objects.create(
        company=infy,
        external_id="uuid-infy-ec-q1",
        doc_type="earnings_call_transcript",
        title="Infosys Q1 FY27 Earnings Call",
        fiscal_period="FY27 Q1",
        period_end_date="2026-06-30",
        total_pages=40,
    )

    # Chunks for INFY AR
    text_risk = (
        "MANAGEMENT DISCUSSION AND ANALYSIS - RISK FACTORS\n"
        "Key risks to long-term revenue growth include client budget consolidation in European banking, "
        "pricing pressure on commodity application maintenance contracts, and wage inflation in digital talent."
    )
    vec_risk = provider.embed_texts([text_risk])[0]
    DocumentChunk.objects.create(
        document=infy_ar,
        chunk_index=0,
        content=text_risk,
        chunk_hash="hash-infy-1",
        section_heading="MANAGEMENT DISCUSSION AND ANALYSIS",
        page_start=12,
        page_end=13,
        char_count=len(text_risk),
        word_count=len(text_risk.split()),
        embedding_model=provider.model_name,
        embedding=vec_risk,
        metadata={"company_ticker": "INFY", "doc_type": "annual_report"},
    )

    text_balance = (
        "BALANCE SHEET AS AT MARCH 31, 2026\n"
        "Cash and cash equivalents stood at INR 24,000 Crores. Total shareholder funds exceeded INR 85,000 Crores."
    )
    vec_balance = provider.embed_texts([text_balance])[0]
    DocumentChunk.objects.create(
        document=infy_ar,
        chunk_index=1,
        content=text_balance,
        chunk_hash="hash-infy-2",
        section_heading="BALANCE SHEET",
        page_start=180,
        page_end=180,
        char_count=len(text_balance),
        word_count=len(text_balance.split()),
        embedding_model=provider.model_name,
        embedding=vec_balance,
        metadata={"company_ticker": "INFY", "doc_type": "annual_report"},
    )

    # Chunk for INFY Transcript
    text_transcript = (
        "QUESTION AND ANSWER SESSION\n"
        "Analyst: Could you comment on the margin trajectory for large deals?\n"
        "CEO: Operating margins were resilient at 21.1%. Large deal pipeline remained robust at $3.2B."
    )
    vec_transcript = provider.embed_texts([text_transcript])[0]
    DocumentChunk.objects.create(
        document=infy_transcript,
        chunk_index=0,
        content=text_transcript,
        chunk_hash="hash-infy-3",
        section_heading="QUESTION AND ANSWER SESSION",
        page_start=5,
        page_end=6,
        char_count=len(text_transcript),
        word_count=len(text_transcript.split()),
        embedding_model=provider.model_name,
        embedding=vec_transcript,
        metadata={"company_ticker": "INFY", "doc_type": "earnings_call_transcript"},
    )

    # 2. Company 2: TCS (for isolation check)
    tcs = Company.objects.create(ticker="TCS", slug="tcs", name="Tata Consultancy Services")
    tcs_ar = FinancialDocument.objects.create(
        company=tcs,
        external_id="uuid-tcs-ar",
        doc_type="annual_report",
        title="TCS Annual Report 2026",
    )
    text_tcs = "TCS reported revenue growth of 8.2% in constant currency terms with strong cloud migration pipeline."
    vec_tcs = provider.embed_texts([text_tcs])[0]
    DocumentChunk.objects.create(
        document=tcs_ar,
        chunk_index=0,
        content=text_tcs,
        chunk_hash="hash-tcs-1",
        section_heading="DIRECTORS REPORT",
        page_start=1,
        page_end=2,
        char_count=len(text_tcs),
        word_count=len(text_tcs.split()),
        embedding_model=provider.model_name,
        embedding=vec_tcs,
        metadata={"company_ticker": "TCS", "doc_type": "annual_report"},
    )

    return {"infy": infy, "tcs": tcs, "provider": provider}


@pytest.mark.django_db
def test_evidence_retrieval_service_ranks_relevant_passage(test_data):
    """Verify evidence retrieval ranks risk passage highest when asked about revenue risks."""
    service = EvidenceRetrievalService(embedding_provider=test_data["provider"])
    result = service.retrieve_evidence(
        ticker="INFY",
        question="What are the key risks to revenue growth and pricing pressure?",
        top_k=3,
        min_score=0.1,
    )

    assert result["has_evidence"] is True
    assert result["ticker"] == "INFY"
    assert len(result["evidence"]) >= 1

    top_item = result["evidence"][0]
    assert "risks to long-term revenue growth" in top_item["content"].lower()
    assert top_item["section_heading"] == "MANAGEMENT DISCUSSION AND ANALYSIS"
    assert top_item["page_start"] == 12
    assert top_item["page_end"] == 13
    assert top_item["document_type"] == "annual_report"
    assert top_item["relevance_score"] > 0


@pytest.mark.django_db
def test_company_filter_isolation(test_data):
    """Enforce company filter: querying INFY must NEVER return TCS chunks."""
    service = EvidenceRetrievalService(embedding_provider=test_data["provider"])
    result = service.retrieve_evidence(
        ticker="INFY",
        question="revenue growth cloud migration",
        top_k=10,
        min_score=0.01,
    )

    for item in result["evidence"]:
        assert item["document_title"] != "TCS Annual Report 2026"
        assert "TCS reported" not in item["content"]


@pytest.mark.django_db
def test_document_type_and_period_filters(test_data):
    """Verify filtering by document_types and fiscal_periods."""
    service = EvidenceRetrievalService(embedding_provider=test_data["provider"])

    # 1. Filter only earnings call transcript
    res_transcript = service.retrieve_evidence(
        ticker="INFY",
        question="What was said about operating margins and deal pipeline?",
        document_types=["earnings_call_transcript"],
        top_k=5,
        min_score=0.1,
    )
    for item in res_transcript["evidence"]:
        assert item["document_type"] == "earnings_call_transcript"

    # 2. Filter only FY26
    res_fy26 = service.retrieve_evidence(
        ticker="INFY",
        question="balance sheet cash and liabilities",
        fiscal_periods=["FY26"],
        top_k=5,
        min_score=0.1,
    )
    for item in res_fy26["evidence"]:
        assert item["fiscal_period"] == "FY26"


@pytest.mark.django_db
def test_missing_evidence_handling(test_data):
    """Verify clean handling when company has no indexed documents or no chunk meets threshold."""
    wipro = Company.objects.create(ticker="WIPRO", slug="wipro", name="Wipro Limited")
    service = EvidenceRetrievalService(embedding_provider=test_data["provider"])

    # Company with 0 chunks
    result = service.retrieve_evidence(ticker="WIPRO", question="revenue growth")
    assert result["has_evidence"] is False
    assert result["total_chunks_searched"] == 0
    assert result["total_evidence_found"] == 0
    assert result["evidence"] == []
    assert "No indexed document chunks found" in result["message"]

    # Extremely high threshold filter
    res_high_thresh = service.retrieve_evidence(
        ticker="INFY",
        question="unrelated quantum teleportation astrophysics",
        min_score=0.99,
    )
    assert res_high_thresh["has_evidence"] is False
    assert res_high_thresh["evidence"] == []


@pytest.mark.django_db
def test_retrieve_api_endpoint(api_client, test_data):
    """Test POST /api/research/retrieve/ API endpoint."""
    url = "/api/research/retrieve/"

    # 1. Success case (POST)
    payload = {
        "ticker": "INFY",
        "question": "What are the major risks to revenue growth?",
        "document_types": ["annual_report"],
        "top_k": 3,
        "min_score": 0.1,
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["ticker"] == "INFY"
    assert data["has_evidence"] is True
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["document_type"] == "annual_report"
    assert "page_start" in data["evidence"][0]

    # 1b. Success case (GET query params)
    get_resp = api_client.get(
        url,
        {
            "ticker": "INFY",
            "question": "What are the major risks to revenue growth?",
            "document_types": "annual_report",
            "top_k": 3,
            "min_score": 0.1,
        },
    )
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["ticker"] == "INFY"
    assert get_resp.json()["has_evidence"] is True

    # 2. Validation error - missing question
    resp_bad = api_client.post(url, {"ticker": "INFY"}, format="json")
    assert resp_bad.status_code == status.HTTP_400_BAD_REQUEST
    assert resp_bad.json()["error"]["code"] == "validation_error"

    # 3. Not found - non-existent company
    from unittest.mock import patch
    from companies.services import CompanyService
    from companies.exceptions import CompanyNotFoundError
    with patch.object(CompanyService, "get_or_resolve_company", side_effect=CompanyNotFoundError("Company 'NONEXISTENT' not found.")):
        resp_404 = api_client.post(url, {"ticker": "NONEXISTENT", "question": "risks"}, format="json")
        assert resp_404.status_code == status.HTTP_404_NOT_FOUND
        assert resp_404.json()["error"]["code"] == "company_not_found"


@pytest.mark.django_db
def test_qualitative_analysis_service_with_mock_llm(test_data):
    """Verify end-to-end qualitative analysis generates categorized findings and verified citations."""
    retrieval_service = EvidenceRetrievalService(embedding_provider=test_data["provider"])
    llm_provider = MockLLMProvider()
    service = QualitativeAnalysisService(
        retrieval_service=retrieval_service,
        llm_provider=llm_provider,
    )

    result = service.analyze_company_question(
        ticker="INFY",
        question="What are the key competitive advantages and long-term revenue risks?",
        top_k=5,
        min_score=0.1,
    )

    assert result["has_sufficient_evidence"] is True
    assert result["company"]["ticker"] == "INFY"
    assert "executive_summary" in result
    assert len(result["key_findings"]) >= 1

    # Verify epistemic categories are present
    categories = {f["category"] for f in result["key_findings"]}
    assert any(c in ("reported_fact", "management_statement", "analytical_interpretation") for c in categories)

    # Verify citation verification
    assert len(result["citations"]) >= 1
    for citation in result["citations"]:
        assert citation["chunk_id"] is not None
        assert citation["document_title"] in ("Infosys Annual Report 2026", "Infosys Q1 FY27 Earnings Call")
        assert citation["page_start"] is not None

    # Verify risks and missing info
    assert len(result["risks_and_uncertainties"]) >= 1
    assert len(result["missing_information_and_limitations"]) >= 1


@pytest.mark.django_db
def test_citation_validation_filters_hallucinated_chunk_ids(test_data):
    """Ensure that if an LLM returns a non-existent or fabricated chunk ID, it is stripped."""
    from unittest.mock import MagicMock

    mock_llm = MagicMock()
    mock_llm.model_name = "test-model"
    mock_llm.generate_analysis.return_value = {
        "executive_summary": "Summary text",
        "key_findings": [
            {
                "claim": "Claim with hallucinated chunk ID",
                "category": "reported_fact",
                "chunk_ids": [999999],  # Does not exist in retrieved evidence
                "quote": "Disclosures indicate stable operating metrics.",
            }
        ],
        "risks_and_uncertainties": ["Macro risk"],
        "missing_information_and_limitations": ["None"],
    }

    retrieval_service = EvidenceRetrievalService(embedding_provider=test_data["provider"])
    service = QualitativeAnalysisService(
        retrieval_service=retrieval_service,
        llm_provider=mock_llm,
    )

    result = service.analyze_company_question(
        ticker="INFY",
        question="revenue risks",
        min_score=0.1,
    )

    # 999999 must not appear in verified citations
    citation_ids = [c["chunk_id"] for c in result["citations"]]
    assert 999999 not in citation_ids


@pytest.mark.django_db
def test_analysis_missing_evidence_handling(test_data):
    """Verify graceful limitation disclosure when company has zero indexed chunks."""
    wipro = Company.objects.create(ticker="WIPRO", slug="wipro", name="Wipro Limited")
    retrieval_service = EvidenceRetrievalService(embedding_provider=test_data["provider"])
    service = QualitativeAnalysisService(
        retrieval_service=retrieval_service,
        llm_provider=MockLLMProvider(),
    )

    result = service.analyze_company_question(
        ticker="WIPRO",
        question="cloud revenue roadmap",
    )

    assert result["has_sufficient_evidence"] is False
    assert result["key_findings"] == []
    assert result["citations"] == []
    assert len(result["missing_information_and_limitations"]) >= 1


@pytest.mark.django_db
def test_analyze_api_endpoint(api_client, test_data):
    """Test POST and GET on /api/research/analyze/."""
    url = "/api/research/analyze/"

    from unittest.mock import patch
    with patch("research.analysis.get_llm_provider", return_value=MockLLMProvider()):
        # 1. Success POST
        payload = {
            "ticker": "INFY",
            "question": "What are the major risks to revenue and margins?",
            "document_types": ["annual_report"],
            "top_k": 5,
            "min_score": 0.1,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["company"]["ticker"] == "INFY"
        assert data["has_sufficient_evidence"] is True
        assert "executive_summary" in data
        assert len(data["key_findings"]) >= 1
        assert len(data["citations"]) >= 1

        # 2. Success GET (query parameters)
        get_resp = api_client.get(
            url,
            {
                "ticker": "INFY",
                "question": "What are the major risks to revenue and margins?",
                "top_k": 3,
                "min_score": 0.1,
            },
        )
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.json()["company"]["ticker"] == "INFY"
        assert get_resp.json()["has_sufficient_evidence"] is True

        # 3. Bad request - missing question
        resp_bad = api_client.post(url, {"ticker": "INFY"}, format="json")
        assert resp_bad.status_code == status.HTTP_400_BAD_REQUEST
        assert resp_bad.json()["error"]["code"] == "validation_error"

        # 4. Not found - non-existent company
        with patch.object(CompanyService, "get_or_resolve_company", side_effect=CompanyNotFoundError("Company 'UNKNOWN_TICKER' not found.")):
            resp_404 = api_client.post(url, {"ticker": "UNKNOWN_TICKER", "question": "risks"}, format="json")
            assert resp_404.status_code == status.HTTP_404_NOT_FOUND
            assert resp_404.json()["error"]["code"] == "company_not_found"

