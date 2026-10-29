from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Core API endpoints
    path("api/", include("core.urls")),

    # Company & Document discovery endpoints
    path("api/companies/", include("companies.urls")),

    # Document indexing & chunks endpoints
    path("api/documents/", include("documents.urls")),

    # Research & evidence retrieval endpoints
    path("api/research/", include("research.urls")),

    # API Documentation (OpenAPI 3 / Swagger / Redoc)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

handler404 = "core.views.custom_404_handler"
handler500 = "core.views.custom_500_handler"
