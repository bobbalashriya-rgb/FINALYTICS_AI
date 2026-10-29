class MarketPingError(Exception):
    """Base exception for all MarketPing integration errors."""
    pass


class MarketPingConnectionError(MarketPingError):
    """Raised when connecting to MarketPing MCP endpoint fails."""
    pass


class MarketPingTimeoutError(MarketPingConnectionError):
    """Raised when a request to MarketPing exceeds timeout limits."""
    pass


class MarketPingToolError(MarketPingError):
    """Raised when an MCP tool invocation returns an error or invalid response."""
    pass


class MarketPingPermissionDeniedError(MarketPingError):
    """Raised when attempting to execute an unpermitted or write tool."""
    pass


class MarketPingRateLimitError(MarketPingError):
    """Raised when MarketPing returns HTTP 429 Too Many Requests or hits rate limits."""
    pass
