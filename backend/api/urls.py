from django.urls import path
from .views import (
    CompanyDetailView,
    PrincipleListView,
    PrincipleDetailView,
    AnalyzeView,
    AskView,
    CompareView,
    ComprehensiveReportView,
    ReportListCreateView,
    ReportDetailView,
    ReportStatusView,
    ReportDownloadView,
    ReportHtmlView,
    ReportMarkdownView,
    UserSubscriptionStatusView,
    WatchlistListCreateView,
    WatchlistDetailView,
    WatchlistCheckView,
    ResearchHistoryListView,
    ResearchHistoryDetailView,
    UserDashboardView,
    AuthRegisterView,
    AuthLoginView,
    AuthLogoutView,
    AuthUserView,
)

urlpatterns = [
    # Core Quantitative
    path('company/<str:ticker>', CompanyDetailView.as_view(), name='company-detail'),
    path('principles', PrincipleListView.as_view(), name='principles-list'),
    path('principles/<str:identifier>', PrincipleDetailView.as_view(), name='principle-detail'),
    path('analyze', AnalyzeView.as_view(), name='analyze'),
    path('ask', AskView.as_view(), name='ask'),
    path('compare', CompareView.as_view(), name='compare'),

    # User Dashboard & Watchlist (Prompt 6)
    path('dashboard', UserDashboardView.as_view(), name='user-dashboard'),
    path('dashboard/', UserDashboardView.as_view(), name='user-dashboard-slash'),
    path('watchlist', WatchlistListCreateView.as_view(), name='watchlist-list-create'),
    path('watchlist/', WatchlistListCreateView.as_view(), name='watchlist-list-create-slash'),
    path('watchlist/check', WatchlistCheckView.as_view(), name='watchlist-check'),
    path('watchlist/check/', WatchlistCheckView.as_view(), name='watchlist-check-slash'),
    path('watchlist/<str:identifier>', WatchlistDetailView.as_view(), name='watchlist-detail'),
    path('watchlist/<str:identifier>/', WatchlistDetailView.as_view(), name='watchlist-detail-slash'),

    # Research Activity / History (Prompt 6)
    path('history', ResearchHistoryListView.as_view(), name='research-history-list'),
    path('history/', ResearchHistoryListView.as_view(), name='research-history-list-slash'),
    path('history/<int:activity_id>', ResearchHistoryDetailView.as_view(), name='research-history-detail'),
    path('history/<int:activity_id>/', ResearchHistoryDetailView.as_view(), name='research-history-detail-slash'),

    # Auth & Account Management
    path('auth/register', AuthRegisterView.as_view(), name='auth-register'),
    path('auth/register/', AuthRegisterView.as_view(), name='auth-register-slash'),
    path('auth/login', AuthLoginView.as_view(), name='auth-login'),
    path('auth/login/', AuthLoginView.as_view(), name='auth-login-slash'),
    path('auth/logout', AuthLogoutView.as_view(), name='auth-logout'),
    path('auth/logout/', AuthLogoutView.as_view(), name='auth-logout-slash'),
    path('auth/user', AuthUserView.as_view(), name='auth-user'),
    path('auth/user/', AuthUserView.as_view(), name='auth-user-slash'),

    # Subscription Status
    path('subscription/status', UserSubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/status/', UserSubscriptionStatusView.as_view(), name='subscription-status-slash'),

    # Quick Synthesized Report (Legacy)
    path('report', ComprehensiveReportView.as_view(), name='report-generate'),
    path('report/<str:ticker>', ComprehensiveReportView.as_view(), name='report-detail'),

    # 15-Section Persistent Research Dossier API
    path('reports', ReportListCreateView.as_view(), name='reports-list-create'),
    path('reports/', ReportListCreateView.as_view(), name='reports-list-create-slash'),
    path('reports/<str:report_id>', ReportDetailView.as_view(), name='reports-detail'),
    path('reports/<str:report_id>/', ReportDetailView.as_view(), name='reports-detail-slash'),
    path('reports/<str:report_id>/status', ReportStatusView.as_view(), name='reports-status'),
    path('reports/<str:report_id>/status/', ReportStatusView.as_view(), name='reports-status-slash'),
    path('reports/<str:report_id>/download', ReportDownloadView.as_view(), name='reports-download'),
    path('reports/<str:report_id>/download/', ReportDownloadView.as_view(), name='reports-download-slash'),
    path('reports/<str:report_id>/html', ReportHtmlView.as_view(), name='reports-html'),
    path('reports/<str:report_id>/markdown', ReportMarkdownView.as_view(), name='reports-markdown'),
]
