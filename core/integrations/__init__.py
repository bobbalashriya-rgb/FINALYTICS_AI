from core.integrations.base import FinancialDataProvider
from core.integrations.marketping.adapter import MarketPingAdapter

_default_provider: FinancialDataProvider | None = None


def get_financial_data_provider() -> FinancialDataProvider:
    """
    Dependency injection factory returning the configured financial data provider.
    Defaults to MarketPingAdapter.
    """
    global _default_provider
    if _default_provider is None:
        _default_provider = MarketPingAdapter()
    return _default_provider
