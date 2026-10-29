import pytest
from rest_framework import status
from rest_framework.test import APIClient

from companies.models import Company
from documents.models import FinancialDocument, DocumentChunk
from core.embeddings.providers import DeterministicLocalEmbeddingProvider
from core.llm.providers import MockLLMProvider
from research.evaluation import AnalysisEvaluator
from research.analysis import QualitativeAnalysisService
from research.services import EvidenceRetrievalService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def evaluation_test_data(db):
    provider = DeterministicLocalEmbeddingProvider(dimension=128)
    company = Company.objects.create(
        ticker="HDFCBANK",
        slug="hdfc-bank",
        name="HDFC Bank Limited",
    )
    doc = FinancialDocument.objects.create(
        company=company,
        external_id="uuid-hdfc-ar",
        doc_type="annual_report",
        title="HDFC Bank Annual Report 2026",
        fiscal_period="FY26",
    )

    text_credit = (
        "MANAGEMENT DISCUSSION AND ANALYSIS\n"
        "Asset quality remained exceptionally healthy with Gross NPA at 1.24% and Net NPA at 0.33%. "
        "Retail advances grew by 18.5% year-on-year driven by digital personal loans and auto financing."
    )
    vec_credit = provider.embed_texts([text_credit])[0]
    c1 = DocumentChunk.objects.create(
        document=doc,
        chunk_index=0,
        content=text_credit,
        chunk_hash="hash-hdfc-1",
        section_heading="MANAGEMENT DISCUSSION AND ANALYSIS",
        page_start=42,
        page_end=43,
        char_count=len(text_credit),
        word_count=len(text_credit.split()),
        embedding_model=provider.model_name,
        embedding=vec_credit,
        metadata={"company_ticker": "HDFCBANK", "doc_type": "annual_report"},
    )

    return {"company": company, "document": doc, "chunk": c1, "provider": provider}


def test_evaluator_high_faithfulness():
    """Verify evaluator reports 1.0 citation accuracy and high quality score when citations are valid."""
    evaluator = AnalysisEvaluator()
    question = "What is the asset quality and retail advance growth?"

    evidence = [
        {
            "chunk_id": 10,
            "document_id": 1,
            "content": "Gross NPA stood at 1.24% and Net NPA at 0.33%. Retail advances grew 18.5%.",
            "relevance_score": 0.85,
        }
    ]

    analysis = {
        "key_findings": [
            {
                "claim": "Gross NPA remained healthy at 1.24%.",
                "category": "reported_fact",
                "chunk_ids": [10],
                "quote": "Gross NPA stood at 1.24%",
            },
            {
                "claim": "Management indicated strong retail credit demand.",
                "category": "management_statement",
                "chunk_ids": [10],
                "quote": "Retail advances grew 18.5%",
            },
        ],
        "missing_information_and_limitations": ["Corporate loan book details not provided."],
    }

    metrics = evaluator.evaluate(question, analysis, evidence)
    assert metrics["overall_quality_score"] > 0.80
    assert metrics["faithfulness_metrics"]["citation_verification_rate"] == 1.0
    assert metrics["faithfulness_metrics"]["supported_claims_ratio"] == 1.0
    assert metrics["faithfulness_metrics"]["unsupported_claims_count"] == 0
    assert metrics["faithfulness_metrics"]["has_hallucinated_citations"] is False


def test_evaluator_detects_hallucinated_citations():
    """Verify evaluator flags hallucinated chunk IDs not present in evidence context."""
    evaluator = AnalysisEvaluator()
    question = "credit quality"

    evidence = [{"chunk_id": 5, "content": "Asset quality text", "relevance_score": 0.7}]
    analysis = {
        "key_findings": [
            {
                "claim": "Unsupported claim referencing ghost chunk",
                "category": "reported_fact",
                "chunk_ids": [999],  # Hallucinated ID
                "quote": "Fake quote",
            }
        ],
        "missing_information_and_limitations": [],
    }

    metrics = evaluator.evaluate(question, analysis, evidence)
    assert metrics["faithfulness_metrics"]["citation_verification_rate"] == 0.0
    assert metrics["faithfulness_metrics"]["hallucinated_citations_count"] == 1
    assert metrics["faithfulness_metrics"]["has_hallucinated_citations"] is True
    assert metrics["faithfulness_metrics"]["unsupported_claims_count"] == 1


from unittest.mock import patch

@pytest.mark.django_db
def test_evaluate_api_endpoint(api_client, evaluation_test_data):
    """Test POST and GET on /api/research/evaluate/."""
    url = "/api/research/evaluate/"

    with patch("research.views.QualitativeAnalysisService") as MockServiceCls:
        # Provide deterministic service behavior for API contract testing
        mock_instance = MockServiceCls.return_value
        mock_instance.analyze_company_question.return_value = {
            "company": {"ticker": "HDFCBANK", "name": "HDFC Bank Limited"},
            "question": "What is the bank's asset quality and Gross NPA ratio?",
            "executive_summary": "Asset quality remained healthy.",
            "key_findings": [
                {
                    "claim": "Gross NPA remained at 1.24%.",
                    "category": "reported_fact",
                    "chunk_ids": [evaluation_test_data["chunk"].id],
                    "quote": "Gross NPA at 1.24%",
                }
            ],
            "citations": [
                {
                    "chunk_id": evaluation_test_data["chunk"].id,
                    "document_id": evaluation_test_data["document"].id,
                    "document_title": "HDFC Bank Annual Report 2026",
                    "document_type": "annual_report",
                    "fiscal_period": "FY26",
                    "page_start": 42,
                    "page_end": 43,
                    "section_heading": "MANAGEMENT DISCUSSION AND ANALYSIS",
                    "source_reference": None,
                }
            ],
            "risks_and_uncertainties": ["Credit risk"],
            "missing_information_and_limitations": ["No retail breakdown"],
            "prompt_version": "v1.0",
            "model_name": "mock-analyst-v1",
            "has_sufficient_evidence": True,
            "total_evidence_chunks_evaluated": 1,
            "metrics": {
                "retrieval_time_ms": 15.2,
                "llm_time_ms": 40.0,
                "total_time_ms": 55.2,
            },
        }

        # 1. Success POST
        payload = {
            "ticker": "HDFCBANK",
            "question": "What is the bank's asset quality and Gross NPA ratio?",
            "top_k": 3,
            "min_score": 0.1,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "analysis" in data
        assert "evaluation" in data
        assert data["analysis"]["company"]["ticker"] == "HDFCBANK"
        assert "metrics" in data["analysis"]
        assert "retrieval_time_ms" in data["analysis"]["metrics"]

        eval_data = data["evaluation"]
        assert "overall_quality_score" in eval_data
        assert "retrieval_metrics" in eval_data
        assert "faithfulness_metrics" in eval_data
        assert eval_data["faithfulness_metrics"]["supported_claims_ratio"] > 0

        # 2. Success GET (query params)
        get_resp = api_client.get(
            url,
            {
                "ticker": "HDFCBANK",
                "question": "asset quality Gross NPA",
                "top_k": 3,
                "min_score": 0.1,
            },
        )
        assert get_resp.status_code == status.HTTP_200_OK
        assert "evaluation" in get_resp.json()
