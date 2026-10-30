import logging
from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint verifying API service availability and database connectivity.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Service Health Check",
        description="Verifies the operational status of the API and its active connection to the PostgreSQL database.",
        responses={
            200: OpenApiResponse(
                description="Application and database are healthy",
            ),
            503: OpenApiResponse(
                description="Database connection is unavailable or degraded",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        db_status = "healthy"
        overall_status = "ok"
        http_status = status.HTTP_200_OK
        details = {}

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            db_status = "unhealthy"
            overall_status = "degraded"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            details["database_error"] = str(exc)

        payload = {
            "status": overall_status,
            "service": "financial-research-api",
            "database": db_status,
        }
        if details:
            payload["details"] = details

        return Response(payload, status=http_status)


def custom_404_handler(request, exception=None):
    """
    Standard JSON 404 response for unrouted URLs.
    """
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "not_found",
                "message": "The requested resource was not found on this server.",
                "details": {"path": request.path},
            },
        },
        status=404,
    )


def custom_500_handler(request):
    """
    Standard JSON 500 response for unhandled server errors.
    """
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected internal server error occurred.",
                "details": None,
            },
        },
        status=500,
    )
