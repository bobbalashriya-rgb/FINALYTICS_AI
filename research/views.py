import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from companies.exceptions import CompanyNotFoundError
from core.integrations.marketping.exceptions import (
    MarketPingConnectionError,
    MarketPingTimeoutError,
    MarketPingRateLimitError,
)
from research.serializers import (
    EvidenceRetrieveRequestSerializer,
    EvidenceRetrieveResponseSerializer,
    QualitativeAnalysisRequestSerializer,
    QualitativeAnalysisResponseSerializer,
    ResearchEvaluationResponseSerializer,
)
from research.services import EvidenceRetrievalService
from research.analysis import QualitativeAnalysisService
from research.evaluation import AnalysisEvaluator

logger = logging.getLogger(__name__)


class EvidenceRetrievalView(APIView):
    """
    Endpoint for evidence retrieval across indexed financial reports.
    Takes a qualitative research question, computes vector and keyword similarity,
    and returns ranked, deduplicated evidence chunks with traceable citations.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Retrieve Evidence for Research Question",
        description=(
            "Retrieves relevant report passages for qualitative research questions without generating an AI answer. "
            "Ranks passages using hybrid semantic vector similarity and keyword overlap, enforces company isolation, "
            "and supports document type and fiscal period filtering."
        ),
        request=EvidenceRetrieveRequestSerializer,
        responses={
            200: EvidenceRetrieveResponseSerializer,
            400: OpenApiResponse(description="Invalid request payload or empty query"),
            404: OpenApiResponse(description="Company not found or unresolved"),
            500: OpenApiResponse(description="Retrieval engine or embedding failure"),
        },
    )
    def _process_retrieval(self, data: dict):
        serializer = EvidenceRetrieveRequestSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid retrieval request parameters.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        ticker = validated["ticker"]
        question = validated["question"]
        doc_types = validated.get("document_types")
        fiscal_periods = validated.get("fiscal_periods")
        top_k = validated.get("top_k", 5)
        min_score = validated.get("min_score", 0.15)

        service = EvidenceRetrievalService()

        try:
            result = service.retrieve_evidence(
                ticker=ticker,
                question=question,
                document_types=doc_types,
                fiscal_periods=fiscal_periods,
                top_k=top_k,
                min_score=min_score,
            )
            return Response(result, status=status.HTTP_200_OK)

        except CompanyNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "company_not_found",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except (MarketPingConnectionError, MarketPingTimeoutError, MarketPingRateLimitError) as exc:
            is_limit = isinstance(exc, MarketPingRateLimitError) or "limit is reached" in str(exc).lower() or "limit_reached" in str(exc).lower()
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_rate_limit_exceeded" if is_limit else "upstream_service_unavailable",
                        "message": (
                            "MarketPing daily free MCP limit is reached (resets at midnight IST). "
                            "Quantitative Deep Dive metrics and ratios remain fully operational."
                            if is_limit
                            else f"MarketPing MCP service unavailable: {str(exc)}"
                        ),
                    },
                    "limit_reached": is_limit,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS if is_limit else status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "bad_request",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Evidence retrieval failed for ticker '%s': %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "retrieval_error",
                        "message": f"Evidence retrieval error: {str(exc)}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Retrieve Evidence for Research Question (POST)",
        description=(
            "Retrieves relevant report passages for qualitative research questions without generating an AI answer. "
            "Ranks passages using hybrid semantic vector similarity and keyword overlap, enforces company isolation, "
            "and supports document type and fiscal period filtering."
        ),
        request=EvidenceRetrieveRequestSerializer,
        responses={
            200: EvidenceRetrieveResponseSerializer,
            400: OpenApiResponse(description="Invalid request payload or empty query"),
            404: OpenApiResponse(description="Company not found or unresolved"),
            500: OpenApiResponse(description="Retrieval engine or embedding failure"),
        },
    )
    def post(self, request, *args, **kwargs):
        return self._process_retrieval(request.data or {})

    @extend_schema(
        summary="Retrieve Evidence for Research Question (GET)",
        description="Allows retrieving evidence via query parameters for quick testing and browser inspection.",
        parameters=[
            EvidenceRetrieveRequestSerializer,
        ],
        responses={
            200: EvidenceRetrieveResponseSerializer,
            400: OpenApiResponse(description="Invalid parameters"),
            404: OpenApiResponse(description="Company not found"),
        },
    )
    def get(self, request, *args, **kwargs):
        data = dict(request.query_params.items())
        # Parse list fields if passed as comma-separated values or repeated params
        if "document_types" in request.query_params:
            doc_types = request.query_params.getlist("document_types")
            if len(doc_types) == 1 and "," in doc_types[0]:
                doc_types = [dt.strip() for dt in doc_types[0].split(",")]
            data["document_types"] = doc_types

        if "fiscal_periods" in request.query_params:
            periods = request.query_params.getlist("fiscal_periods")
            if len(periods) == 1 and "," in periods[0]:
                periods = [p.strip() for p in periods[0].split(",")]
            data["fiscal_periods"] = periods

        return self._process_retrieval(data)


class QualitativeAnalysisView(APIView):
    """
    Endpoint for evidence-grounded qualitative fundamental analysis.
    Retrieves verified corporate disclosures and earnings call excerpts,
    synthesizes findings into categorized claims (facts, statements, interpretations)
    using an LLM, and enforces verifiable citations with traceable page numbers.
    """
    permission_classes = []
    authentication_classes = []

    def _process_analysis(self, data: dict):
        serializer = QualitativeAnalysisRequestSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid analysis request parameters.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        ticker = validated["ticker"]
        question = validated["question"]
        doc_types = validated.get("document_types")
        fiscal_periods = validated.get("fiscal_periods")
        top_k = validated.get("top_k", 8)
        min_score = validated.get("min_score", 0.15)

        service = QualitativeAnalysisService()

        try:
            result = service.analyze_company_question(
                ticker=ticker,
                question=question,
                document_types=doc_types,
                fiscal_periods=fiscal_periods,
                top_k=top_k,
                min_score=min_score,
            )
            return Response(result, status=status.HTTP_200_OK)

        except CompanyNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "company_not_found",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except (MarketPingConnectionError, MarketPingTimeoutError, MarketPingRateLimitError) as exc:
            is_limit = isinstance(exc, MarketPingRateLimitError) or "limit is reached" in str(exc).lower() or "limit_reached" in str(exc).lower()
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_rate_limit_exceeded" if is_limit else "upstream_service_unavailable",
                        "message": (
                            "MarketPing daily free MCP limit is reached (resets at midnight IST). "
                            "Quantitative Deep Dive metrics and ratios remain fully operational."
                            if is_limit
                            else f"MarketPing MCP service unavailable: {str(exc)}"
                        ),
                    },
                    "limit_reached": is_limit,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS if is_limit else status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "bad_request",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Qualitative analysis failed for ticker '%s': %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "analysis_error",
                        "message": f"Qualitative analysis generation error: {str(exc)}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Generate Qualitative Fundamental Analysis (POST)",
        description=(
            "Generates evidence-grounded fundamental analysis for a company using retrieved financial report excerpts. "
            "Distinguishes reported facts, management statements, and analytical interpretations with verifiable page citations."
        ),
        request=QualitativeAnalysisRequestSerializer,
        responses={
            200: QualitativeAnalysisResponseSerializer,
            400: OpenApiResponse(description="Invalid request parameters"),
            404: OpenApiResponse(description="Company not found"),
            500: OpenApiResponse(description="Analysis generation failure"),
        },
    )
    def post(self, request, *args, **kwargs):
        return self._process_analysis(request.data or {})

    @extend_schema(
        summary="Generate Qualitative Fundamental Analysis (GET)",
        description="Allows running analysis via query parameters for browser and Postman convenience.",
        parameters=[
            QualitativeAnalysisRequestSerializer,
        ],
        responses={
            200: QualitativeAnalysisResponseSerializer,
            400: OpenApiResponse(description="Invalid request parameters"),
            404: OpenApiResponse(description="Company not found"),
        },
    )
    def get(self, request, *args, **kwargs):
        data = dict(request.query_params.items())
        if "document_types" in request.query_params:
            doc_types = request.query_params.getlist("document_types")
            if len(doc_types) == 1 and "," in doc_types[0]:
                doc_types = [dt.strip() for dt in doc_types[0].split(",")]
            data["document_types"] = doc_types

        if "fiscal_periods" in request.query_params:
            periods = request.query_params.getlist("fiscal_periods")
            if len(periods) == 1 and "," in periods[0]:
                periods = [p.strip() for p in periods[0].split(",")]
            data["fiscal_periods"] = periods

        return self._process_analysis(data)


class ResearchEvaluationView(APIView):
    """
    Endpoint for evaluating retrieval relevance, grounding, citation accuracy,
    and faithfulness of qualitative fundamental analysis.
    """
    permission_classes = []
    authentication_classes = []

    def _process_evaluation(self, data: dict):
        serializer = QualitativeAnalysisRequestSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid evaluation request parameters.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        ticker = validated["ticker"]
        question = validated["question"]
        doc_types = validated.get("document_types")
        fiscal_periods = validated.get("fiscal_periods")
        top_k = validated.get("top_k", 8)
        min_score = validated.get("min_score", 0.15)

        retrieval_service = EvidenceRetrievalService()
        analysis_service = QualitativeAnalysisService(retrieval_service=retrieval_service)
        evaluator = AnalysisEvaluator()

        try:
            # 1. Fetch retrieval candidates
            retrieval_res = retrieval_service.retrieve_evidence(
                ticker=ticker,
                question=question,
                document_types=doc_types,
                fiscal_periods=fiscal_periods,
                top_k=top_k,
                min_score=min_score,
            )
            evidence_items = retrieval_res.get("evidence", [])

            # 2. Run analysis
            analysis_res = analysis_service.analyze_company_question(
                ticker=ticker,
                question=question,
                document_types=doc_types,
                fiscal_periods=fiscal_periods,
                top_k=top_k,
                min_score=min_score,
            )

            # 3. Evaluate faithfulness and retrieval metrics
            eval_metrics = evaluator.evaluate(
                question=question,
                analysis_result=analysis_res,
                retrieved_evidence=evidence_items,
            )

            return Response(
                {
                    "analysis": analysis_res,
                    "evaluation": eval_metrics,
                },
                status=status.HTTP_200_OK,
            )

        except CompanyNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "company_not_found",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except (MarketPingConnectionError, MarketPingTimeoutError, MarketPingRateLimitError) as exc:
            is_limit = isinstance(exc, MarketPingRateLimitError) or "limit is reached" in str(exc).lower() or "limit_reached" in str(exc).lower()
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_rate_limit_exceeded" if is_limit else "upstream_service_unavailable",
                        "message": (
                            "MarketPing daily free MCP limit is reached (resets at midnight IST). "
                            "Quantitative Deep Dive metrics and ratios remain fully operational."
                            if is_limit
                            else f"MarketPing MCP service unavailable: {str(exc)}"
                        ),
                    },
                    "limit_reached": is_limit,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS if is_limit else status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "bad_request",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Research evaluation failed for ticker '%s': %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "evaluation_error",
                        "message": f"Evaluation error: {str(exc)}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Evaluate Qualitative Analysis & Faithfulness (POST)",
        description=(
            "Runs evidence retrieval, qualitative analysis, and formal evaluation of retrieval relevance, "
            "citation accuracy, and grounding faithfulness in a single request."
        ),
        request=QualitativeAnalysisRequestSerializer,
        responses={
            200: ResearchEvaluationResponseSerializer,
            400: OpenApiResponse(description="Invalid request parameters"),
            404: OpenApiResponse(description="Company not found"),
            500: OpenApiResponse(description="Evaluation failure"),
        },
    )
    def post(self, request, *args, **kwargs):
        return self._process_evaluation(request.data or {})

    @extend_schema(
        summary="Evaluate Qualitative Analysis & Faithfulness (GET)",
        description="Allows running evaluation via query parameters.",
        parameters=[
            QualitativeAnalysisRequestSerializer,
        ],
        responses={
            200: ResearchEvaluationResponseSerializer,
            400: OpenApiResponse(description="Invalid request parameters"),
            404: OpenApiResponse(description="Company not found"),
        },
    )
    def get(self, request, *args, **kwargs):
        data = dict(request.query_params.items())
        if "document_types" in request.query_params:
            doc_types = request.query_params.getlist("document_types")
            if len(doc_types) == 1 and "," in doc_types[0]:
                doc_types = [dt.strip() for dt in doc_types[0].split(",")]
            data["document_types"] = doc_types

        if "fiscal_periods" in request.query_params:
            periods = request.query_params.getlist("fiscal_periods")
            if len(periods) == 1 and "," in periods[0]:
                periods = [p.strip() for p in periods[0].split(",")]
            data["fiscal_periods"] = periods

        return self._process_evaluation(data)
