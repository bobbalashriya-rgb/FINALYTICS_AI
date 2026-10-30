import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from core.integrations.marketping.client import MarketPingClient
from core.integrations.marketping.exceptions import (
    MarketPingConnectionError,
    MarketPingTimeoutError,
    MarketPingRateLimitError,
    MarketPingPermissionDeniedError,
)


def test_mcp_client_permission_denied_for_write_tool():
    """Verify write or unapproved tools are rejected before network invocation."""
    client = MarketPingClient()
    with pytest.raises(MarketPingPermissionDeniedError) as exc_info:
        client.call_tool("delete_all_filings", {})
    assert "not in the allowed read-only tools whitelist" in str(exc_info.value)


def test_mcp_client_timeout_handling():
    """Verify timeout triggers MarketPingTimeoutError with retry attempts."""
    client = MarketPingClient(timeout_seconds=0.05, max_retries=1)

    async def slow_operation():
        await asyncio.sleep(0.5)
        return "done"

    with pytest.raises(MarketPingTimeoutError) as exc_info:
        client._run_async(client._execute_with_retry(slow_operation))

    assert "timed out after 0.05s" in str(exc_info.value)


def test_mcp_client_rate_limit_detection():
    """Verify HTTP 429 / Rate Limit error is detected and raised as MarketPingRateLimitError."""
    client = MarketPingClient(max_retries=0)

    async def rate_limited_call():
        raise RuntimeError("HTTP 429: Too Many Requests. Rate limit exceeded.")

    with pytest.raises(MarketPingRateLimitError) as exc_info:
        client._run_async(client._execute_with_retry(rate_limited_call))

    assert "rate limit reached (429)" in str(exc_info.value)


def test_mcp_client_connection_error():
    """Verify network connection failures trigger MarketPingConnectionError."""
    client = MarketPingClient(max_retries=0)

    async def broken_connection():
        raise ConnectionResetError("Connection refused by remote host")

    with pytest.raises(MarketPingConnectionError) as exc_info:
        client._run_async(client._execute_with_retry(broken_connection))

    assert "MarketPing MCP connection failed" in str(exc_info.value)
