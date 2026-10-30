# Finlytics AI - Django REST Framework Backend

This directory (`backend/`) is the **Django** and **Django REST Framework (DRF)** service. It provides 100% API compatibility with the React frontend.

---

## 🚀 Key Features & Conversions

- **Framework**: Built on **Django 5.x** & **Django REST Framework (DRF)**.
- **ORM & Database**: Powered by **PostgreSQL** via **Django ORM** (`InvestmentPrinciple` model) with psycopg2/psycopg support and automatic migration handling.
- **Auto-Seeding**: Automatic population of default institutional investment principles via `post_migrate` signal, JSON fixture (`fixtures/principles.json`), and custom management command.
- **Built-in Admin Interface**: Full CRUD administration of investment principles and thresholds at `/admin/`.
- **CORS Support**: Integrated `django-cors-headers` allowing frontend calls from Vite dev (`:5173`) and production domains.
- **Complete Pipeline Services**: Preserved all institutional financial research services:
  - `company_data.py`: Yfinance statement extraction and normalization.
  - `financial_metrics.py`: Deterministic metric engine (ROE, ROCE, Debt/Equity, FCF, Margins, P/E).
  - `investment_principles.py`: Mathematical evaluation against configured principles.
  - `ai_research.py`: Gemini-powered qualitative thesis and zero-fail algorithmic fallback engine.

---

## 📁 Project Structure

```
backend/
├── manage.py                          # Django CLI utility
├── requirements.txt                   # Production dependencies (PostgreSQL + DRF)
├── .env.example                       # Environment configuration template
├── finolitics_project/                # Core Django project configuration
│   ├── settings.py                    # CORS, DRF, PostgreSQL, and app settings
│   ├── urls.py                        # Root URL routing
│   ├── wsgi.py                        # WSGI production entrypoint
│   └── asgi.py                        # ASGI entrypoint
└── api/                               # Main application app
    ├── models.py                      # InvestmentPrinciple Django model
    ├── admin.py                       # Django Admin configuration
    ├── serializers.py                 # DRF Serializers for API requests/responses
    ├── views.py                       # DRF APIViews (endpoints)
    ├── urls.py                        # API route mappings (/api/*)
    ├── apps.py                        # App config with auto-seeding signal
    ├── fixtures/                      # Seed data fixtures (principles.json)
    ├── tests.py                       # Automated test suite
    ├── management/commands/
    │   └── seed_principles.py         # Custom command: python manage.py seed_principles
    └── services/                      # Pure Python analytical and AI services
        ├── company_data.py
        ├── financial_metrics.py
        ├── investment_principles.py
        └── ai_research.py
```

---

## 🛠 Local Setup & Running

### 1. Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure PostgreSQL & Environment
Start your local PostgreSQL service or use Docker:
```bash
# Optional: run postgres via docker from project root
docker compose up -d
```
Or create the database locally with Homebrew PostgreSQL:
```bash
createdb finolitics
```

Copy `.env.example` to `.env` and set your PostgreSQL credentials:
```bash
cp .env.example .env
```

Postgres configuration options in `.env`:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=finolitics
DB_USER=postgres       # Or your local macOS username (e.g. shriya)
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
# Alternatively:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/finolitics
```

### 3. Run Migrations & Seed Database
```bash
python manage.py migrate
```
*(The default 6 investment principles are automatically seeded during migration!)*

You can also re-seed or reset principles at any time:
```bash
python manage.py seed_principles
# or reload from fixture
python manage.py loaddata api/fixtures/principles.json
```

### 4. (Optional) Create Admin User
```bash
python manage.py createsuperuser
```

### 5. Start Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 🧪 Running Tests
```bash
python manage.py test api
```

---

## 🔌 API Endpoints Reference

All endpoints match the FastAPI contract under the `/api/` prefix:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check & framework info |
| `GET` | `/api/principles` | List all configured investment principles |
| `PUT` | `/api/principles/<id>` | Update threshold for a principle |
| `GET` | `/api/company/<ticker>` | Fetch normalized Yfinance statements for a ticker |
| `POST` | `/api/analyze` | Run full Single Analysis pipeline (`{"ticker": "AAPL"}`) |
| `POST` | `/api/compare` | Run head-to-head Peer Comparison (`{"tickers": ["TCS.NS", "INFY.NS"]}`) |
| `POST` | `/api/ask` | Interactive Q&A on company analysis context |
| `GET` | `/admin/` | Django Administration portal |

