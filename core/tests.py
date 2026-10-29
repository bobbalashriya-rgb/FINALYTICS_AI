import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_health_check_healthy(api_client):
    """
    Test GET /api/health/ returns 200 OK and expected structure when DB is healthy.
    """
    url = reverse("health-check")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "financial-research-api"
    assert data["database"] == "healthy"


@pytest.mark.django_db
def test_health_check_database_failure(api_client):
    """
    Test GET /api/health/ returns 503 Service Unavailable when DB is unreachable.
    """
    url = reverse("health-check")

    with patch("core.views.connection.cursor", side_effect=Exception("Database connection timeout")):
        response = api_client.get(url)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["status"] == "degraded"
    assert data["service"] == "financial-research-api"
    assert data["database"] == "unhealthy"
    assert "database_error" in data.get("details", {})


def test_schema_endpoint(api_client):
    """
    Test GET /api/schema/ generates valid OpenAPI schema.
    """
    url = reverse("schema")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "openapi" in response.data or "openapi" in response.content.decode()


def test_swagger_documentation_endpoint(api_client):
    """
    Test GET /api/docs/ returns Swagger UI HTML.
    """
    url = reverse("swagger-ui")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert b"swagger-ui" in response.content.lower()


def test_not_found_error_format(api_client):
    """
    Test unrouted endpoint returns standardized error format.
    """
    response = api_client.get("/api/non-existent-endpoint/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "not_found"
    assert "message" in data["error"]
