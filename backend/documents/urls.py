from django.urls import path
from documents.views import (
    DocumentIndexView,
    DocumentChunksListView,
)

urlpatterns = [
    # Document indexing (Chunk & Embed)
    path(
        "<str:document_id>/index/",
        DocumentIndexView.as_view(),
        name="document-index",
    ),
    # Document chunks inspector
    path(
        "<str:document_id>/chunks/",
        DocumentChunksListView.as_view(),
        name="document-chunks-list",
    ),
]
