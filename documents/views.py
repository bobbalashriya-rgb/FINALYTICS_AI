import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from companies.services import CompanyService
from companies.exceptions import CompanyNotFoundError
from documents.models import FinancialDocument, DocumentPage, DocumentChunk
from documents.services import DocumentDiscoveryService
from documents.ingestion import DocumentIngestionService
from documents.chunking import FinancialDocumentChunker, DocumentIndexingService
from documents.serializers import (
    AvailableDocumentsResponseSerializer,
    DocumentIngestRequestSerializer,
    DocumentIngestResponseSerializer,
    DocumentPageSerializer,
    DocumentChunkSerializer,
    DocumentIndexRequestSerializer,
    DocumentIndexResponseSerializer,
)
from core.integrations.marketping.exceptions import MarketPingConnectionError, MarketPingTimeoutError

logger = logging.getLogger(__name__)


def find_document(document_id: str, company=None):
    """
    Finds a document by primary key ID or MarketPing external UUID,
    optionally scoped to a specific company.
    """
    qs = FinancialDocument.objects.all()
    if company is not None:
        qs = qs.filter(company=company)
    if str(document_id).isdigit():
        doc = qs.filter(id=int(document_id)).first()
        if doc:
            return doc
    return qs.filter(external_id=str(document_id)).first()


def find_document_for_company(company, document_id: str):
    """
    Finds a document belonging to a company by local numeric ID or MarketPing external UUID.
    """
    return find_document(document_id, company=company)


class CompanyAvailableDocumentsView(APIView):
    """
    Endpoint discovering and listing available financial reports for a company.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="List Available Financial Reports for Company",
        description=(
            "Retrieves verified financial reports (Annual Reports, Quarterly Results, Earnings Call Transcripts) "
            "discovered through MarketPing MCP."
        ),
        parameters=[
            OpenApiParameter(
                name="doc_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by document type (e.g. annual_report, earnings_call_transcript, financial_results, investor_presentation, announcement, brsr)",
                required=False,
            ),
            OpenApiParameter(
                name="sync",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Sync latest documents from MarketPing (default true)",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Maximum number of documents to return (default 50)",
                required=False,
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Pagination offset (default 0)",
                required=False,
            ),
        ],
        responses={
            200: AvailableDocumentsResponseSerializer,
            404: OpenApiResponse(description="Company not found"),
            503: OpenApiResponse(description="MarketPing MCP failure"),
        },
    )
    def get(self, request, ticker, *args, **kwargs):
        doc_type = request.query_params.get("doc_type")
        sync_param = request.query_params.get("sync", "true").lower() in ("true", "1")
        try:
            limit = max(1, min(100, int(request.query_params.get("limit", 50))))
        except ValueError:
            limit = 50
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            offset = 0

        company_service = CompanyService()
        doc_service = DocumentDiscoveryService()

        # 1. Resolve company
        try:
            company = company_service.get_or_resolve_company(query=ticker)
        except CompanyNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "company_not_found",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except (MarketPingConnectionError, MarketPingTimeoutError) as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_service_error",
                        "message": f"MarketPing MCP service error: {exc}",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # 2. Retrieve / sync available documents
        try:
            documents_qs = doc_service.get_available_documents(
                company=company, doc_type=doc_type, sync=sync_param
            )
            total_count = documents_qs.count()
            paginated_docs = documents_qs[offset : offset + limit]

            serializer = AvailableDocumentsResponseSerializer(
                {
                    "company": company,
                    "total": total_count,
                    "results": paginated_docs,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except (MarketPingConnectionError, MarketPingTimeoutError) as exc:
            logger.error("MarketPing document discovery error for %s: %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_service_error",
                        "message": f"Failed to retrieve reports from MarketPing: {exc}",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Unexpected error retrieving documents for %s: %s", ticker, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred while retrieving company documents.",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentIngestionView(APIView):
    """
    Endpoint retrieving and ingesting actual report page content from MarketPing MCP into PostgreSQL.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Ingest Document Page Content",
        description=(
            "Retrieves indexed page text from MarketPing MCP for a financial report and stores "
            "it idempotently in PostgreSQL. Page numbers, content hashes, and tabular layouts are preserved."
        ),
        request=DocumentIngestRequestSerializer,
        responses={
            200: DocumentIngestResponseSerializer,
            400: OpenApiResponse(description="Invalid ingestion parameters"),
            404: OpenApiResponse(description="Company or document not found"),
            503: OpenApiResponse(description="MarketPing MCP connection failure"),
        },
    )
    def post(self, request, ticker, document_id, *args, **kwargs):
        serializer = DocumentIngestRequestSerializer(data=request.data or {})
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid ingestion parameters.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        page_from = serializer.validated_data.get("page_from")
        page_to = serializer.validated_data.get("page_to")
        max_pages = serializer.validated_data.get("max_pages", 24)
        ingest_all = serializer.validated_data.get("ingest_all", False)

        company_service = CompanyService()

        # 1. Resolve company
        try:
            company = company_service.get_or_resolve_company(query=ticker)
        except CompanyNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "company_not_found",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except (MarketPingConnectionError, MarketPingTimeoutError) as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_service_error",
                        "message": f"MarketPing MCP service error: {exc}",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # 2. Locate document
        doc = find_document_for_company(company, document_id)
        if not doc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "document_not_found",
                        "message": f"Document '{document_id}' not found for company '{ticker}'.",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 3. Perform ingestion
        ingestion_service = DocumentIngestionService()
        try:
            result = ingestion_service.ingest_document(
                document=doc,
                page_from=page_from,
                page_to=page_to,
                max_batch_pages=max_pages,
                ingest_all=ingest_all,
            )
            return Response(result, status=status.HTTP_200_OK)

        except (MarketPingConnectionError, MarketPingTimeoutError) as exc:
            logger.error("MarketPing ingestion error for doc %s: %s", document_id, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "upstream_service_error",
                        "message": f"Failed to retrieve pages from MarketPing MCP: {exc}",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Unexpected error during document ingestion for %s: %s", document_id, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred during document ingestion.",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentPagesListView(APIView):
    """
    Endpoint listing the stored page content and metadata for an ingested document.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="List Ingested Document Pages",
        description="Retrieves the stored page content, word counts, and page numbers for an ingested document.",
        parameters=[
            OpenApiParameter(
                name="page_number",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by specific page number",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Max pages to return (default: 20)",
                required=False,
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Pagination offset (default: 0)",
                required=False,
            ),
        ],
        responses={
            200: DocumentPageSerializer(many=True),
            404: OpenApiResponse(description="Company or document not found"),
        },
    )
    def get(self, request, ticker, document_id, *args, **kwargs):
        company_service = CompanyService()

        try:
            company = company_service.get_or_resolve_company(query=ticker)
        except CompanyNotFoundError as exc:
            return Response(
                {"success": False, "error": {"code": "company_not_found", "message": str(exc)}},
                status=status.HTTP_404_NOT_FOUND,
            )

        doc = find_document_for_company(company, document_id)
        if not doc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "document_not_found",
                        "message": f"Document '{document_id}' not found for company '{ticker}'.",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        pages_qs = DocumentPage.objects.filter(document=doc)
        page_num = request.query_params.get("page_number")
        if page_num and str(page_num).isdigit():
            pages_qs = pages_qs.filter(page_number=int(page_num))

        try:
            limit = max(1, min(100, int(request.query_params.get("limit", 20))))
        except ValueError:
            limit = 20
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            offset = 0

        total_pages = pages_qs.count()
        paginated_pages = pages_qs[offset : offset + limit]

        serializer = DocumentPageSerializer(paginated_pages, many=True)
        return Response(
            {
                "document_id": doc.id,
                "external_id": doc.external_id,
                "title": doc.title,
                "ingestion_status": doc.ingestion_status,
                "total_stored_pages": total_pages,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class DocumentIndexView(APIView):
    """
    Endpoint for section-aware document chunking and vector embedding indexing.
    Chunks ingested document pages, computes vector embeddings via the configured
    embedding provider, and stores chunks idempotently in PostgreSQL.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Index Financial Document (Chunk & Embed)",
        description=(
            "Chunks all ingested pages of a financial document using section-aware boundaries, "
            "computes vector embeddings via the configured provider, and stores them in PostgreSQL with "
            "traceable source metadata (company, doc_type, fiscal_period, page ranges)."
        ),
        request=DocumentIndexRequestSerializer,
        responses={
            200: DocumentIndexResponseSerializer,
            400: OpenApiResponse(description="Document has no ingested pages or bad request parameters"),
            404: OpenApiResponse(description="Document or Company not found"),
            500: OpenApiResponse(description="Embedding provider failure or indexing error"),
        },
    )
    def post(self, request, document_id, ticker=None, *args, **kwargs):
        company = None
        if ticker:
            company_service = CompanyService()
            try:
                company = company_service.get_or_resolve_company(query=ticker)
            except CompanyNotFoundError as exc:
                return Response(
                    {"success": False, "error": {"code": "company_not_found", "message": str(exc)}},
                    status=status.HTTP_404_NOT_FOUND,
                )

        doc = find_document(document_id, company=company)
        if not doc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "document_not_found",
                        "message": f"Document '{document_id}' not found.",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DocumentIndexRequestSerializer(data=request.data or {})
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid indexing parameters.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        force_reindex = validated.get("force_reindex", False)
        target_chunk_chars = validated.get("target_chunk_chars", 1000)
        overlap_chars = validated.get("overlap_chars", 150)

        chunker = FinancialDocumentChunker(
            target_chunk_chars=target_chunk_chars,
            overlap_chars=overlap_chars,
        )
        service = DocumentIndexingService(chunker=chunker)

        try:
            result = service.index_document(document=doc, force_reindex=force_reindex)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "indexing_validation_error",
                        "message": str(exc),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Document indexing failed for document %s: %s", doc.id, exc)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "indexing_error",
                        "message": f"Document indexing failed: {str(exc)}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentChunksListView(APIView):
    """
    Read-only view for inspecting the generated chunks and traceable metadata of an indexed document.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="List Indexed Document Chunks",
        description="Retrieves paginated chunks with section headings, page ranges, and metadata for an indexed document.",
        parameters=[
            OpenApiParameter(
                name="page_number",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter chunks covering a specific page number",
                required=False,
            ),
            OpenApiParameter(
                name="heading",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter chunks containing heading keyword",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Max chunks to return (default: 20)",
                required=False,
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Pagination offset (default: 0)",
                required=False,
            ),
        ],
        responses={
            200: DocumentChunkSerializer(many=True),
            404: OpenApiResponse(description="Document not found"),
        },
    )
    def get(self, request, document_id, ticker=None, *args, **kwargs):
        company = None
        if ticker:
            company_service = CompanyService()
            try:
                company = company_service.get_or_resolve_company(query=ticker)
            except CompanyNotFoundError as exc:
                return Response(
                    {"success": False, "error": {"code": "company_not_found", "message": str(exc)}},
                    status=status.HTTP_404_NOT_FOUND,
                )

        doc = find_document(document_id, company=company)
        if not doc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "document_not_found",
                        "message": f"Document '{document_id}' not found.",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chunks_qs = DocumentChunk.objects.filter(document=doc)

        page_num = request.query_params.get("page_number")
        if page_num and str(page_num).isdigit():
            p = int(page_num)
            chunks_qs = chunks_qs.filter(page_start__lte=p, page_end__gte=p)

        heading_filter = request.query_params.get("heading")
        if heading_filter:
            chunks_qs = chunks_qs.filter(section_heading__icontains=heading_filter)

        try:
            limit = max(1, min(100, int(request.query_params.get("limit", 20))))
        except ValueError:
            limit = 20
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            offset = 0

        total_chunks = chunks_qs.count()
        paginated_chunks = chunks_qs[offset : offset + limit]
        serializer = DocumentChunkSerializer(paginated_chunks, many=True)

        return Response(
            {
                "document_id": doc.id,
                "external_id": doc.external_id,
                "title": doc.title,
                "indexed_chunks_count": doc.indexed_chunks_count,
                "last_indexed_at": doc.last_indexed_at.isoformat() if doc.last_indexed_at else None,
                "total_matched_chunks": total_chunks,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
