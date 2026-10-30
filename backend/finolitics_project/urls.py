from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def root_view(request):
    db_status = "connected"
    pg_version = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            row = cursor.fetchone()
            if row:
                pg_version = row[0]
    except Exception as e:
        db_status = f"error: {str(e)}"

    return JsonResponse({
        "message": "Finlytics AI Platform API is running. Access /api/ for endpoints, /api/docs/ for Swagger UI.",
        "version": "1.0.0",
        "framework": "Django REST Framework",
        "database": {
            "engine": connection.vendor,
            "status": db_status,
            "version": pg_version
        },
        "modules": {
            "quantitative": "/api/",
            "companies": "/api/companies/",
            "documents": "/api/documents/",
            "qualitative_research": "/api/research/",
            "swagger_docs": "/api/docs/"
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),

    # Quantitative & User Management endpoints (both with and without /api/ prefix)
    path('api/', include('api.urls')),
    path('', include('api.urls')),

    # Core system endpoints
    path('api/', include('core.urls')),
    path('api/core/', include('core.urls')),
    path('core/', include('core.urls')),

    # Qualitative fundamental RAG endpoints
    path('api/companies/', include('companies.urls')),
    path('companies/', include('companies.urls')),
    path('api/documents/', include('documents.urls')),
    path('documents/', include('documents.urls')),
    path('api/research/', include('research.urls')),
    path('research/', include('research.urls')),

    # API Documentation (OpenAPI 3 / Swagger / Redoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('health', root_view, name='root-health'),
    path('', root_view, name='root'),
]
