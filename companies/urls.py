from django.urls import path
from companies.views import CompanyDetailView
from documents.views import (
    CompanyAvailableDocumentsView,
    DocumentIngestionView,
    DocumentPagesListView,
    DocumentIndexView,
    DocumentChunksListView,
)

urlpatterns = [
    # Company resolution & detail
    path(
        "<str:ticker>/",
        CompanyDetailView.as_view(),
        name="company-detail",
    ),

    # Company available financial reports
    path(
        "<str:ticker>/documents/available/",
        CompanyAvailableDocumentsView.as_view(),
        name="company-documents-available",
    ),

    # Document content ingestion
    path(
        "<str:ticker>/documents/<str:document_id>/ingest/",
        DocumentIngestionView.as_view(),
        name="document-ingest",
    ),

    # Ingested document pages viewer
    path(
        "<str:ticker>/documents/<str:document_id>/pages/",
        DocumentPagesListView.as_view(),
        name="document-pages-list",
    ),

    # Document chunking & embedding indexing
    path(
        "<str:ticker>/documents/<str:document_id>/index/",
        DocumentIndexView.as_view(),
        name="company-document-index",
    ),

    # Document chunks inspector
    path(
        "<str:ticker>/documents/<str:document_id>/chunks/",
        DocumentChunksListView.as_view(),
        name="company-document-chunks-list",
    ),
]
