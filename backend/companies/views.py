import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from companies.services import CompanyService
from companies.serializers import CompanySerializer
from companies.exceptions import CompanyNotFoundError
from core.integrations.marketping.exceptions import MarketPingConnectionError, MarketPingTimeoutError

logger = logging.getLogger(__name__)


class CompanyDetailView(APIView):
    """
    Endpoint resolving and retrieving an Indian listed company by its ticker or name.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Resolve and Retrieve Company Information",
        description=(
            "Resolves an Indian listed company by ticker symbol (e.g. INFY, TCS) or name. "
            "Fetches verified identity from MarketPing MCP and caches in PostgreSQL."
        ),
        parameters=[
            OpenApiParameter(
                name="refresh",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Force re-resolution from MarketPing MCP instead of reading cache",
                required=False,
            ),
        ],
        responses={
            200: CompanySerializer,
            404: OpenApiResponse(description="Company not found"),
            503: OpenApiResponse(description="MarketPing MCP connection failure"),
        },
    )
    def get(self, request, ticker, *args, **kwargs):
        force_refresh = request.query_params.get("refresh", "false").lower() in ("true", "1")
        service = CompanyService()

        try:
            company = service.get_or_resolve_company(
                query=ticker, force_refresh=force_refresh
            )
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)

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
        except (MarketPingConnectionError, MarketPingTimeoutError) as exc:
            logger.error("MarketPing MCP error resolving company %s: %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_service_error",
                        "message": f"MarketPing MCP service error: {exc}",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Unexpected error resolving company %s: %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred while resolving the company.",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
