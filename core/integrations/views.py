import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from core.integrations import get_financial_data_provider
from core.integrations.marketping.exceptions import MarketPingError

logger = logging.getLogger(__name__)


class MarketPingStatusView(APIView):
    """
    Diagnostic status endpoint verifying connectivity to the remote MarketPing MCP server.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="MarketPing Connection Status",
        description="Pings the remote MarketPing MCP endpoint and measures round-trip protocol handshake latency.",
        responses={
            200: OpenApiResponse(description="MarketPing MCP is reachable and responsive"),
            503: OpenApiResponse(description="MarketPing MCP is unreachable or timed out"),
        },
    )
    def get(self, request, *args, **kwargs):
        provider = get_financial_data_provider()
        try:
            diagnostic = provider.check_connection()
            return Response(diagnostic, status=status.HTTP_200_OK)
        except MarketPingError as exc:
            logger.error("MarketPing connection check failed: %s", exc)
            return Response(
                {
                    "status": "disconnected",
                    "provider": "MarketPing",
                    "error": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Unexpected error during MarketPing status check: %s", exc)
            return Response(
                {
                    "status": "disconnected",
                    "provider": "MarketPing",
                    "error": "Failed to connect to MarketPing MCP.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class MarketPingToolsView(APIView):
    """
    Developer diagnostic endpoint listing the permitted read-only tools and verified schemas.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="List Permitted MarketPing Tools",
        description="Returns discovered MarketPing tools restricted strictly to read-only capabilities with their input schemas.",
        responses={
            200: OpenApiResponse(description="List of discovered and permitted tools"),
            503: OpenApiResponse(description="Failed to query tools from MarketPing"),
        },
    )
    def get(self, request, *args, **kwargs):
        provider = get_financial_data_provider()
        try:
            tools = provider.list_tools()
            return Response(
                {
                    "provider": "MarketPing",
                    "allowed_tools_count": len(tools),
                    "tools": tools,
                },
                status=status.HTTP_200_OK,
            )
        except MarketPingError as exc:
            logger.error("MarketPing tools discovery failed: %s", exc)
            return Response(
                {
                    "status": "error",
                    "provider": "MarketPing",
                    "error": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Unexpected error during MarketPing tools discovery: %s", exc)
            return Response(
                {
                    "status": "error",
                    "provider": "MarketPing",
                    "error": "Failed to discover MarketPing tools.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
