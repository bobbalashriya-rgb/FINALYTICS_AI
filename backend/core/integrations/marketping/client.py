import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from core.integrations.marketping.exceptions import (
    MarketPingConnectionError,
    MarketPingPermissionDeniedError,
    MarketPingTimeoutError,
    MarketPingToolError,
    MarketPingRateLimitError,
)

logger = logging.getLogger(__name__)

ALLOWED_READONLY_TOOLS = {
    "resolve_company",
    "company_snapshot",
    "list_documents",
    "doc_contents",
    "read_pages",
    "search_filings",
}


class MarketPingClient:
    """
    Low-level client for the MarketPing remote MCP server using official Python MCP SDK.
    Enforces read-only tool restrictions, timeouts, and controlled retries.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: int = 2,
    ):
        self.endpoint_url = endpoint_url or os.getenv(
            "MARKETPING_MCP_URL", "https://mcp.marketping.in/mcp"
        )
        self.timeout_seconds = timeout_seconds or float(
            os.getenv("MARKETPING_TIMEOUT_SECONDS", "15.0")
        )
        self.max_retries = max_retries
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _run_async(self, coro):
        """
        Safely execute an async coroutine from synchronous Django execution context.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already inside an active event loop (e.g. pytest-asyncio), run in a separate thread
            return self._executor.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)

    async def _execute_with_retry(self, async_func):
        """
        Execute an async operation with timeout and exponential backoff retry.
        """
        attempt = 0
        last_exception = None

        while attempt <= self.max_retries:
            attempt += 1
            try:
                return await asyncio.wait_for(
                    async_func(), timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError as exc:
                last_exception = MarketPingTimeoutError(
                    f"MarketPing MCP request timed out after {self.timeout_seconds}s (attempt {attempt}/{self.max_retries + 1})"
                )
                logger.warning(
                    "MarketPing timeout on attempt %d: %s", attempt, exc
                )
            except Exception as exc:
                actual_exc = exc
                while hasattr(actual_exc, "exceptions") and actual_exc.exceptions:
                    actual_exc = actual_exc.exceptions[0]
                if isinstance(actual_exc, MarketPingRateLimitError):
                    logger.warning("MarketPing rate limit reached: %s", actual_exc)
                    raise actual_exc
                err_str = str(actual_exc).lower()
                if (
                    "429" in err_str
                    or "rate limit" in err_str
                    or "too many requests" in err_str
                    or "limit is reached" in err_str
                    or "limit_reached" in err_str
                    or "daily mcp limit" in err_str
                ):
                    last_exception = MarketPingRateLimitError(
                        f"MarketPing MCP rate limit reached (429): {actual_exc}"
                    )
                    logger.warning("MarketPing rate limit reached (not retrying): %s", actual_exc)
                    raise last_exception
                else:
                    last_exception = MarketPingConnectionError(
                        f"MarketPing MCP connection failed: {actual_exc}"
                    )
                    logger.warning(
                        "MarketPing connection error on attempt %d: %s", attempt, actual_exc
                    )

            if attempt <= self.max_retries:
                backoff = 0.5 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        raise last_exception

    async def _async_check_connection(self) -> Dict[str, Any]:
        async def _check():
            start_time = time.perf_counter()
            async with streamable_http_client(self.endpoint_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    init_result = await session.initialize()
                    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    return {
                        "status": "connected",
                        "provider": "MarketPing",
                        "endpoint": self.endpoint_url,
                        "protocol_version": init_result.protocol_version,
                        "server_name": init_result.server_info.name,
                        "server_version": init_result.server_info.version,
                        "latency_ms": latency_ms,
                    }

        return await self._execute_with_retry(_check)

    def check_connection(self) -> Dict[str, Any]:
        """
        Synchronous connection diagnostic check.
        """
        return self._run_async(self._async_check_connection())

    async def _async_list_tools(self) -> List[Dict[str, Any]]:
        async def _list():
            async with streamable_http_client(self.endpoint_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    allowed_tools = []
                    for tool in tools_result.tools:
                        if tool.name in ALLOWED_READONLY_TOOLS:
                            allowed_tools.append(
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "input_schema": tool.input_schema,
                                }
                            )
                    return allowed_tools

        return await self._execute_with_retry(_list)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Synchronous tool discovery restricted to allowed read-only tools.
        """
        return self._run_async(self._async_list_tools())

    async def _async_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name not in ALLOWED_READONLY_TOOLS:
            raise MarketPingPermissionDeniedError(
                f"Tool '{tool_name}' is not in the allowed read-only tools whitelist."
            )

        async def _call():
            async with streamable_http_client(self.endpoint_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    if result.is_error:
                        err_text = ""
                        for item in (result.content or []):
                            err_text += getattr(item, "text", str(item)) + " "
                        err_text = err_text.strip()
                        if (
                            "limit is reached" in err_text.lower()
                            or "limit_reached" in err_text.lower()
                            or "daily mcp limit" in err_text.lower()
                        ):
                            raise MarketPingRateLimitError(
                                f"MarketPing daily limit reached: {err_text}"
                            )
                        raise MarketPingToolError(
                            f"Tool '{tool_name}' returned error: {err_text or result.content}"
                        )
                    # Extract contents
                    content_list = []
                    for item in result.content:
                        if hasattr(item, "text"):
                            content_list.append(item.text)
                        else:
                            content_list.append(str(item))
                    return content_list

        return await self._execute_with_retry(_call)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute an allowed read-only MCP tool with parameters.
        """
        return self._run_async(self._async_call_tool(tool_name, arguments))
