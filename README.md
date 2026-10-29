# Financial Report RAG Backend for Indian Listed Companies

A backend application for qualitative fundamental analysis of Indian listed companies using financial reports (Annual Reports, Quarterly Results, and Earnings Call Transcripts) retrieved through **MarketPing MCP** and analyzed via an evidence-grounded Retrieval-Augmented Generation (RAG) architecture.

---

## 1. Architectural Highlights

- **Single Modular Django Backend**: Classical Django architecture with modular business applications (`companies`, `documents`, `research`, `core`), without microservice complexity.
- **Official MarketPing Remote MCP Integration**: Connects via the official Python MCP SDK with strict read-only tool restrictions, exponential backoff retries, and rate-limit detection.
- **Section-Aware Financial Chunking**: Detects Indian corporate filing sections (MD&A, Auditor's Report, Balance Sheet, P&L, Notes to Financial Statements, Corporate Governance, BRSR, and Earnings Call Q&As) while preserving exact page number attribution.
- **Flexible Embeddings**:
  - `DeterministicLocalEmbeddingProvider`: Fast, 768-dimensional token & n-gram feature hashing for 100% offline development with zero API costs.
  - `OpenAIEmbeddingProvider` (`text-embedding-3-small`) & `GeminiEmbeddingProvider` (`text-embedding-004`).
- **Hybrid Evidence Retrieval**: Dense cosine similarity combined with lexical keyword boosts, strictly enforced company isolation, and document-type / fiscal-period filtering.
- **Three-Tier Epistemic Analysis**:
  - `reported_fact`: Audited numbers, balance sheet figures, contractual commitments.
  - `management_statement`: Leadership assertions, forward-looking guidance, executive claims.
  - `analytical_interpretation`: Objective financial reasoning connecting facts or evaluating statements.
- **Hallucination Prevention & Citation Verification**: Every claim cites specific chunk IDs with document titles and page ranges. Hallucinated chunk IDs are stripped and flagged.
- **Quantitative Evaluation Engine**: Evaluates retrieval relevance (hit rate, keyword coverage) and answer faithfulness (citation verification rate, supported claims ratio).
- **Prohibits Buy/Sell Recommendations**: Dedicated strictly to objective fundamental research.

---

## 2. Directory Structure

```
StockQualitativeAnalysis/
├── companies/                 # Company resolution, ticker mapping, and persistence
│   ├── models.py              # Company model
│   ├── services.py            # Resolution service via MarketPing MCP
│   └── views.py               # Company detail and lookup API
├── documents/                 # Report discovery, ingestion, chunking, and embedding
│   ├── models.py              # FinancialDocument, DocumentPage, DocumentChunk
│   ├── ingestion.py           # Content ingestion and text normalization
│   ├── chunking.py            # Section-aware chunking and indexing service
│   └── views.py               # Ingestion, indexing, and chunk inspection APIs
├── research/                  # Evidence retrieval, LLM analysis, and evaluation
│   ├── services.py            # Hybrid evidence retrieval service
│   ├── prompts.py             # Version-controlled prompt (v1.0) & system rules
│   ├── analysis.py            # Grounded analysis orchestrator & citation validator
│   ├── evaluation.py          # Faithfulness and retrieval evaluation engine
│   └── views.py               # Retrieve, Analyze, and Evaluate endpoints
├── core/                      # Shared infrastructure, MCP client, and LLM providers
│   ├── integrations/          # MarketPing MCP client wrapper and adapter
│   ├── embeddings/            # Local, OpenAI, and Gemini embedding providers
│   └── llm/                   # Gemini, OpenAI, and Mock LLM providers
├── config/                    # Django project settings, ASGI/WSGI, and root URLs
├── pytest.ini                 # Pytest test configuration
├── requirements.txt           # Project dependencies
└── README.md                  # System documentation
```

---

## 3. Prerequisites & Installation

### Requirements
- **Python**: 3.11 – 3.14
- **PostgreSQL**: 16+
- **Virtual Environment Tool**: `venv`

### Step 1: Clone and Create Virtual Environment
```powershell
cd StockQualitativeAnalysis
python -m venv venv
.\venv\Scripts\activate
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 4. Configuration (`.env`)

Create a `.env` file in the project root (see `.env.example`):

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secure-django-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DB_NAME=financial_research_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=127.0.0.1
DB_PORT=5432

# MarketPing Remote MCP
MARKETPING_MCP_URL=https://mcp.marketping.in/mcp

# Embedding Provider Configuration
# Options: "local" (default offline hashing), "openai", or "gemini"
EMBEDDING_PROVIDER=local

# LLM Provider Configuration
# Options: "gemini" (default if key present), "openai", or "mock" (offline fallback)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_LLM_MODEL=gemini-2.5-flash

# OpenAI Settings (required only if LLM_PROVIDER=openai or EMBEDDING_PROVIDER=openai)
OPENAI_API_KEY=your_openai_api_key
OPENAI_LLM_MODEL=gpt-4o-mini
```

---

## 5. Database Setup & Migrations

```powershell
# Run migrations
python manage.py migrate

# (Optional) Verify system configuration
python manage.py check
```

---

## 6. Running the Application

```powershell
python manage.py runserver
```

- API Base: `http://127.0.0.1:8000/api/`
- Interactive Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc Documentation: `http://127.0.0.1:8000/api/redoc/`

---

## 7. API Reference & Postman Workflows

### Phase 1: System Health
- **`GET /api/health/`**
  - Verifies application and database connectivity.
  - Response: `{"status": "ok", "service": "financial-research-api", "database": "connected"}`

### Phase 2: MarketPing Connection Status
- **`GET /api/integrations/marketping/status/`**
  - Verifies MCP connection and lists discoverable read-only tools.
- **`GET /api/integrations/marketping/tools/`**
  - Lists permitted tools and schemas.

### Phase 3: Company Resolution & Document Discovery
- **`GET /api/companies/{ticker}/`**
  - Resolves and saves an Indian listed company (e.g. `/api/companies/INFY/`).
- **`GET /api/companies/{ticker}/documents/available/`**
  - Discovers verified Annual Reports, Results, and Transcripts.
  - Query parameters: `?doc_type=annual_report&sync=true`

### Phase 4: Report Content Ingestion
- **`POST /api/companies/{ticker}/documents/{document_id}/ingest/`**
  - Ingests report pages with text normalization and SHA-256 deduplication.
  - Payload:
    ```json
    {
      "page_from": 1,
      "page_to": 24,
      "max_pages": 24
    }
    ```
- **`GET /api/companies/{ticker}/documents/{document_id}/pages/`**
  - Inspects ingested pages with exact page numbering and character counts.

### Phase 5: Document Chunking & Vector Indexing
- **`POST /api/documents/{document_id}/index/`**
  - Chunks stored pages by section boundaries, computes embeddings, and saves chunks idempotently.
  - Payload:
    ```json
    {
      "force_reindex": false,
      "target_chunk_chars": 1000,
      "overlap_chars": 150
    }
    ```
- **`GET /api/documents/{document_id}/chunks/`**
  - Inspects generated chunks with section headings, page spans, and metadata.

### Phase 6: Evidence Retrieval API
- **`POST /api/research/retrieve/`** *(or GET with query params)*
  - Retrieves ranked, deduplicated evidence passages with citations.
  - Payload:
    ```json
    {
      "ticker": "INFY",
      "question": "What are the major risks to revenue growth and margins?",
      "document_types": ["annual_report"],
      "top_k": 5,
      "min_score": 0.15
    }
    ```

### Phase 7: Qualitative Fundamental Analysis API
- **`POST /api/research/analyze/`** *(or GET with query params)*
  - Generates evidence-grounded fundamental analysis with citations.
  - Payload:
    ```json
    {
      "ticker": "INFY",
      "question": "What are the company's main competitive advantages and long-term risks?",
      "document_types": ["annual_report"],
      "top_k": 8
    }
    ```
  - Response includes:
    - `executive_summary`
    - `key_findings` (categorized into `reported_fact`, `management_statement`, `analytical_interpretation`)
    - `citations` (verified chunk IDs, document titles, page spans)
    - `risks_and_uncertainties`
    - `missing_information_and_limitations`
    - `metrics` (retrieval time, LLM time, total execution time)

### Phase 8: RAG Evaluation & Faithfulness API
- **`POST /api/research/evaluate/`** *(or GET with query params)*
  - Executes retrieval, analysis, and formal quantitative evaluation in a single call.
  - Payload:
    ```json
    {
      "ticker": "INFY",
      "question": "What are the major risks to revenue growth?",
      "top_k": 5
    }
    ```
  - Response includes:
    - Full `analysis`
    - `evaluation`:
      - `overall_quality_score` (0.0 to 1.0)
      - `retrieval_metrics` (`retrieval_hit_rate`, `mean_relevance_score`, `keyword_coverage_ratio`)
      - `faithfulness_metrics` (`citation_verification_rate`, `supported_claims_ratio`, `hallucinated_citations_count`, `limitations_disclosed`)

---

## 8. Automated Test Suite

All tests can be executed offline using pytest:

```powershell
pytest
```

### Test Suite Structure
- `companies/tests.py`: Company resolution, persistence, and error handling.
- `documents/tests.py` & `documents/test_ingestion.py`: Metadata discovery, page retrieval, and text normalization.
- `documents/test_chunking.py` & `documents/test_resilience.py`: Section-aware chunking, giant page wrapping, empty page skipping, and indexing idempotency.
- `core/test_integrations.py` & `core/test_resilience.py`: MarketPing tool whitelisting, timeouts, connection errors, and HTTP 429 rate limits.
- `research/tests.py`: Evidence retrieval, company filter isolation, and qualitative analysis.
- `research/test_evaluation.py`: Faithfulness scoring, hallucinated citation detection, and evaluation endpoint verification.

**Current Test Status**: **55 passed in 6.96s** (100% pass rate).
