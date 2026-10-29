import json
import logging
from typing import Any, Dict, List, Optional

from core.integrations.base import FinancialDataProvider
from core.integrations.marketping.client import MarketPingClient

logger = logging.getLogger(__name__)


class MarketPingAdapter(FinancialDataProvider):
    """
    Adapter implementing FinancialDataProvider for MarketPing remote MCP service.
    Translates high-level domain operations into verified MarketPing tool invocations.
    """

    def __init__(self, client: Optional[MarketPingClient] = None):
        self.client = client or MarketPingClient()

    def _parse_tool_output(self, raw_output: Any) -> Any:
        """
        Parses JSON strings from tool text output if applicable.
        """
        if isinstance(raw_output, list) and len(raw_output) == 1:
            item = raw_output[0]
            if isinstance(item, str):
                try:
                    return json.loads(item)
                except Exception:
                    return item
        return raw_output

    def check_connection(self) -> Dict[str, Any]:
        return self.client.check_connection()

    def list_tools(self) -> List[Dict[str, Any]]:
        return self.client.list_tools()

    def resolve_company(self, query: str) -> List[Dict[str, Any]]:
        raw = self.client.call_tool("resolve_company", {"query": query})
        parsed = self._parse_tool_output(raw)
        if isinstance(parsed, dict) and "matches" in parsed:
            return parsed["matches"]
        return parsed if isinstance(parsed, list) else [parsed]

    def get_company_snapshot(self, company: str) -> Dict[str, Any]:
        raw = self.client.call_tool("company_snapshot", {"company": company})
        parsed = self._parse_tool_output(raw)
        return parsed if isinstance(parsed, dict) else {"raw": parsed}

    def list_documents(
        self, company: str, doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        args: Dict[str, Any] = {"company": company}
        if doc_type:
            args["doc_type"] = doc_type
        raw = self.client.call_tool("list_documents", args)
        parsed = self._parse_tool_output(raw)
        if isinstance(parsed, dict) and "documents" in parsed:
            return parsed["documents"]
        return parsed if isinstance(parsed, list) else [parsed]

    def get_document_contents(self, doc_id: str) -> Dict[str, Any]:
        raw = self.client.call_tool("doc_contents", {"doc_id": doc_id})
        parsed = self._parse_tool_output(raw)
        return parsed if isinstance(parsed, dict) else {"raw": parsed}

    def read_pages(
        self, doc_id: str, page_from: int, page_to: Optional[int] = None
    ) -> Dict[str, Any]:
        args: Dict[str, Any] = {"doc_id": doc_id, "page_from": page_from}
        if page_to is not None:
            args["page_to"] = page_to
        raw = self.client.call_tool("read_pages", args)
        parsed = self._parse_tool_output(raw)
        return parsed if isinstance(parsed, dict) else {"raw": parsed}

    def search_filings(
        self, query: str, company: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        args: Dict[str, Any] = {"query": query}
        if company:
            args["company"] = company
        raw = self.client.call_tool("search_filings", args)
        parsed = self._parse_tool_output(raw)
        return parsed if isinstance(parsed, list) else [parsed]
