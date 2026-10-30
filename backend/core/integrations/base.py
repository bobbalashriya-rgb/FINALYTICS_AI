from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class FinancialDataProvider(ABC):
    """
    Abstract interface for financial data and document providers.
    Decouples business services from MarketPing-specific MCP protocol details.
    """

    @abstractmethod
    def check_connection(self) -> Dict[str, Any]:
        """
        Check connectivity and latency to the data provider.
        """
        pass

    @abstractmethod
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List discovered and permitted tools from the provider.
        """
        pass

    @abstractmethod
    def resolve_company(self, query: str) -> List[Dict[str, Any]]:
        """
        Find Indian listed company candidates by name, ticker, or partial match.
        """
        pass

    @abstractmethod
    def get_company_snapshot(self, company: str) -> Dict[str, Any]:
        """
        Retrieve fundamentals and valuation snapshot for a company slug/ticker.
        """
        pass

    @abstractmethod
    def list_documents(
        self, company: str, doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve available documents for a company.
        """
        pass

    @abstractmethod
    def get_document_contents(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve table of contents and page outline for a document.
        """
        pass

    @abstractmethod
    def read_pages(
        self, doc_id: str, page_from: int, page_to: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve actual text content of a page range (max 12 pages).
        """
        pass

    @abstractmethod
    def search_filings(
        self, query: str, company: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search document filings across reports and transcripts.
        """
        pass
