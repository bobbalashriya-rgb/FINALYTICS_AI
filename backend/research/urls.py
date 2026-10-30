from django.urls import path
from research.views import (
    EvidenceRetrievalView,
    QualitativeAnalysisView,
    ResearchEvaluationView,
)

urlpatterns = [
    # Qualitative evidence retrieval (Phase 6)
    path(
        "retrieve/",
        EvidenceRetrievalView.as_view(),
        name="research-retrieve",
    ),

    # Evidence-grounded qualitative fundamental analysis (Phase 7)
    path(
        "analyze/",
        QualitativeAnalysisView.as_view(),
        name="research-analyze",
    ),

    # RAG evaluation and faithfulness scoring (Phase 8)
    path(
        "evaluate/",
        ResearchEvaluationView.as_view(),
        name="research-evaluate",
    ),
]
