from django.urls import path
from core.views import HealthCheckView
from core.integrations.views import MarketPingStatusView, MarketPingToolsView

urlpatterns = [
    # Health check
    path("health/", HealthCheckView.as_view(), name="health-check"),

    # MarketPing MCP integration diagnostics
    path(
        "integrations/marketping/status/",
        MarketPingStatusView.as_view(),
        name="marketping-status",
    ),
    path(
        "integrations/marketping/tools/",
        MarketPingToolsView.as_view(),
        name="marketping-tools",
    ),
]
