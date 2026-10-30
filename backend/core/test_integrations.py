import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.integrations.marketping.client import (
    ALLOWED_READONLY_TOOLS,
    MarketPingClient,
)
from core.integrations.marketping.exceptions import (
    MarketPingConnectionError,
    MarketPingPermissionDeniedError,
)
from core.integrations.marketping.adapter import MarketPingAdapter


@pytest.fixture
def api_client():
    return APIClient()


def test_allowed_readonly_tools_whitelist():
    """Verify strictly defined read-only tools whitelist."""
    expected = {
        "resolve_company",
        "company_snapshot",
        "list_documents",
        "doc_contents",
        "read_pages",
        "search_filings",
    }
    assert ALLOWED_READONLY_TOOLS == expected


def test_marketping_disallows_unpermitted_tools():
    """Verify that calling an arbitrary or write tool is rejected immediately."""
    client = MarketPingClient()
    with pytest.raises(MarketPingPermissionDeniedError) as exc_info:
        client.call_tool("watchlist_add", {"company": "infy"})

    assert "not in the allowed read-only tools whitelist" in str(exc_info.value)


def test_marketping_status_view_success(api_client):
    """Test GET /api/integrations/marketping/status/ returns 200 with diagnostics."""
    mock_diagnostic = {
        "status": "connected",
        "provider": "MarketPing",
        "endpoint": "https://mcp.marketping.in/mcp",
        "protocol_version": "2025-11-25",
        "server_name": "marketping",
        "server_version": "1.0.0",
        "latency_ms": 125.4,
    }

    with patch(
        "core.integrations.views.get_financial_data_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.check_connection.return_value = mock_diagnostic
        mock_get_provider.return_value = mock_provider

        response = api_client.get(reverse("marketping-status"))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "connected"
        assert data["server_name"] == "marketping"
        assert data["latency_ms"] == 125.4


def test_marketping_status_view_failure(api_client):
    """Test GET /api/integrations/marketping/status/ returns 503 when disconnected."""
    with patch(
        "core.integrations.views.get_financial_data_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.check_connection.side_effect = MarketPingConnectionError(
            "Connection refused"
        )
        mock_get_provider.return_value = mock_provider

        response = api_client.get(reverse("marketping-status"))
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "disconnected"
        assert "Connection refused" in data["error"]


def test_marketping_tools_view_success(api_client):
    """Test GET /api/integrations/marketping/tools/ returns 200 and tool list."""
    mock_tools = [
        {
            "name": "resolve_company",
            "description": "Find company by name or ticker",
            "input_schema": {"type": "object"},
        },
        {
            "name": "list_documents",
            "description": "List documents for company",
            "input_schema": {"type": "object"},
        },
    ]

    with patch(
        "core.integrations.views.get_financial_data_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.list_tools.return_value = mock_tools
        mock_get_provider.return_value = mock_provider

        response = api_client.get(reverse("marketping-tools"))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["provider"] == "MarketPing"
        assert data["allowed_tools_count"] == 2
        assert len(data["tools"]) == 2
        assert data["tools"][0]["name"] == "resolve_company"


def test_marketping_adapter_methods():
    """Test MarketPingAdapter maps high-level calls to client tool calls."""
    mock_client = MagicMock()
    mock_client.call_tool.return_value = ['[{"slug": "tcs", "name": "Tata Consultancy Services"}]']

    adapter = MarketPingAdapter(client=mock_client)
    res = adapter.resolve_company("TCS")

    mock_client.call_tool.assert_called_once_with("resolve_company", {"query": "TCS"})
    assert isinstance(res, list)
    assert res[0]["slug"] == "tcs"
