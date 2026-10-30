import os
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import pypdf

from api.models import InvestmentPrinciple, ResearchReport, ReportSection, SavedCompany, ResearchActivity
from companies.models import Company
from documents.models import FinancialDocument, DocumentChunk
from core.embeddings.providers import DeterministicLocalEmbeddingProvider
from core.llm.providers import MockLLMProvider
from api.services.report_generator import InstitutionalReportGenerator
from api.services.company_data import (
    CompanyProfile,
    FinancialStatements,
    HistoricalPrice,
    NormalizedCompanyData,
    FinancialDataError,
)

User = get_user_model()


def get_mock_company_data(ticker="AAPL"):
    profile = CompanyProfile(
        ticker=ticker,
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        current_price=185.50,
        market_cap=2800000000000,
        currency="USD",
        shares_outstanding=15500000000,
        enterprise_value=2850000000000,
        forward_pe=28.5,
        trailing_pe=30.2,
        peg_ratio=2.1,
        price_to_sales=7.5,
        price_to_book=45.0,
        ev_to_ebitda=22.0,
        ev_to_revenue=7.6,
        book_value=4.12,
        beta=1.1,
    )
    financials = FinancialStatements(
        income_statement={
            "2023": {
                "Total Revenue": 383285000000,
                "Net Income": 96995000000,
                "Operating Income": 114301000000,
                "Gross Profit": 169148000000,
                "EBITDA": 125820000000,
            },
            "2022": {
                "Total Revenue": 394328000000,
                "Net Income": 99803000000,
                "Operating Income": 119437000000,
                "Gross Profit": 170782000000,
                "EBITDA": 130541000000,
            },
        },
        balance_sheet={
            "2023": {
                "Total Assets": 352583000000,
                "Total Liabilities Net Minority Interest": 290437000000,
                "Stockholders Equity": 62146000000,
                "Total Debt": 111088000000,
                "Cash And Cash Equivalents": 29965000000,
                "Current Assets": 143566000000,
                "Current Liabilities": 145308000000,
            },
            "2022": {
                "Total Assets": 352755000000,
                "Total Liabilities Net Minority Interest": 302083000000,
                "Stockholders Equity": 50672000000,
                "Total Debt": 120069000000,
                "Cash And Cash Equivalents": 23646000000,
                "Current Assets": 135405000000,
                "Current Liabilities": 153982000000,
            },
        },
        cash_flow={
            "2023": {
                "Operating Cash Flow": 110543000000,
                "Free Cash Flow": 99584000000,
                "Capital Expenditure": -10959000000,
            },
            "2022": {
                "Operating Cash Flow": 122151000000,
                "Free Cash Flow": 111443000000,
                "Capital Expenditure": -10708000000,
            },
        },
    )
    prices = [
        HistoricalPrice(date="2024-01-02", open=187.1, high=188.4, low=183.8, close=185.6, volume=82488700),
        HistoricalPrice(date="2024-01-03", open=184.2, high=185.8, low=183.4, close=184.2, volume=58414500),
    ]
    return NormalizedCompanyData(profile=profile, financials=financials, historical_prices=prices)


class ApiEndpointsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_root_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("Finlytics", data["message"])
        self.assertIn("modules", data)
        self.assertIn("quantitative", data["modules"])
        self.assertIn("qualitative_research", data["modules"])

    def test_principles_list(self):
        response = self.client.get('/api/principles')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 6)
        identifiers = [p['identifier'] for p in data]
        self.assertIn('ROE_GT_15', identifiers)
        self.assertIn('PE_LT_30', identifiers)

    def test_update_principle(self):
        response = self.client.put(
            '/api/principles/ROE_GT_15',
            data={"threshold": 0.20},
            format="json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["threshold"], 0.20)

        # Verify in DB
        p = InvestmentPrinciple.objects.get(identifier='ROE_GT_15')
        self.assertEqual(p.threshold, 0.20)

    @patch('api.views.answer_financial_question')
    def test_ask_endpoint(self, mock_answer):
        mock_answer.return_value = "The ROE of this company is 18%."
        mock_context = {
            "profile": {"name": "Test Corp", "ticker": "TEST"},
            "metrics": {"roe": 0.18, "revenue_growth": 0.12},
            "evaluations": {"passed_count": 5, "total_count": 6}
        }
        response = self.client.post(
            '/api/ask',
            data={"question": "What is the ROE of this company?", "context": mock_context},
            format="json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertEqual(data["answer"], "The ROE of this company is 18%.")

    def test_analyze_empty_ticker(self):
        response = self.client.post(
            '/api/analyze',
            data={"ticker": ""},
            format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_compare_invalid_tickers(self):
        response = self.client.post(
            '/api/compare',
            data={"tickers": ["AAPL"]},
            format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_report_empty_ticker(self):
        response = self.client.post(
            '/api/report',
            data={"ticker": ""},
            format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())


class ResearchReportBackendTestCase(TestCase):
    """
    Exhaustive tests for Research Report Generation feature:
    - User authentication and ownership isolation
    - 50-page maximum limit enforcement
    - Database persistence of ResearchReport and 15 ReportSections
    - Private file storage (unrestricted public URLs forbidden)
    - Reproducible research snapshot integrity
    - Real-time status, download, and delete endpoints
    - Failure handling
    """
    def setUp(self):
        self.user1 = User.objects.create_user(username="analyst_alice", password="password123")
        self.user2 = User.objects.create_user(username="analyst_bob", password="password456")
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.anon_client = APIClient()

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests to reports endpoints must be denied (401 Unauthorized or 403 Forbidden)."""
        res_list = self.anon_client.get('/api/reports')
        self.assertIn(res_list.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        res_post = self.anon_client.post('/api/reports', data={"ticker": "AAPL"}, format="json")
        self.assertIn(res_post.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        res_detail = self.anon_client.get('/api/reports/1')
        self.assertIn(res_detail.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        res_status = self.anon_client.get('/api/reports/1/status')
        self.assertIn(res_status.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        res_download = self.anon_client.get('/api/reports/1/download')
        self.assertIn(res_download.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @patch('api.services.report_generator.fetch_company_data')
    def test_report_generation_and_persistence(self, mock_fetch):
        """Authenticated user generates report; verifies DB models, 15 sections, and 50-page cap."""
        mock_fetch.return_value = get_mock_company_data("AAPL")

        response = self.client1.post(
            '/api/reports',
            data={"ticker": "AAPL", "report_title": "Apple Institutional Deep Dive"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        report_id = data["report_id"]
        self.assertTrue(report_id)
        self.assertEqual(data["ticker"], "AAPL")
        self.assertEqual(data["status"], "completed")

        # 1. Verify Database Persistence of ResearchReport
        report = ResearchReport.objects.get(report_id=report_id)
        self.assertEqual(report.user, self.user1)
        self.assertEqual(report.ticker, "AAPL")
        self.assertEqual(report.status, "completed")
        self.assertEqual(report.page_limit, 50)
        self.assertLessEqual(report.page_count, 50)
        self.assertGreater(report.page_count, 0)
        self.assertTrue(report.private_file_path)

        # 2. Verify all 15 ReportSections are created with correct sequence and titles
        sections = report.sections.all().order_by("section_number")
        self.assertEqual(sections.count(), 15)
        expected_keys = [
            "cover_page",
            "executive_summary",
            "company_overview",
            "investment_thesis",
            "financial_performance",
            "absolute_valuation",
            "growth_adjusted_valuation",
            "historical_valuation",
            "relative_valuation",
            "dcf_valuation",
            "valuation_risk",
            "qualitative_findings",
            "opportunities_and_risks",
            "conclusion",
            "sources_disclaimers",
        ]
        for idx, sec in enumerate(sections, start=1):
            self.assertEqual(sec.section_number, idx)
            self.assertEqual(sec.section_key, expected_keys[idx - 1])
            self.assertTrue(len(sec.title) > 0)
            self.assertTrue(len(sec.content_markdown) > 0)

        # 3. Verify Research Snapshot Integrity for total reproducibility
        snapshot = report.research_snapshot
        self.assertIn("profile", snapshot)
        self.assertIn("metrics", snapshot)
        self.assertIn("valuation_modules", snapshot)
        self.assertIn("principles", snapshot)
        self.assertIn("qualitative", snapshot)
        self.assertEqual(snapshot["profile"]["ticker"], "AAPL")

        # 4. Verify Programmatic PDF Page Verification <= 50
        self.assertTrue(os.path.exists(report.private_file_path))
        reader = pypdf.PdfReader(report.private_file_path)
        actual_pdf_pages = len(reader.pages)
        self.assertLessEqual(actual_pdf_pages, 50)
        self.assertEqual(report.page_count, actual_pdf_pages)

    @patch('api.services.report_generator.fetch_company_data')
    def test_user_ownership_and_isolation(self, mock_fetch):
        """User B must NEVER be able to view, download, check status, or delete User A's reports."""
        mock_fetch.return_value = get_mock_company_data("MSFT")

        # User 1 generates report
        res = self.client1.post('/api/reports', data={"ticker": "MSFT"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        report_id = res.json()["report_id"]
        report_pk = res.json()["id"]

        # User 2 attempts to view User 1's report via UUID -> 404
        res_view_uuid = self.client2.get(f'/api/reports/{report_id}')
        self.assertEqual(res_view_uuid.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts to view User 1's report via primary key -> 404
        res_view_pk = self.client2.get(f'/api/reports/{report_pk}')
        self.assertEqual(res_view_pk.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts to check status -> 404
        res_status = self.client2.get(f'/api/reports/{report_id}/status')
        self.assertEqual(res_status.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts unauthorized download -> 404
        res_download = self.client2.get(f'/api/reports/{report_id}/download')
        self.assertEqual(res_download.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts unauthorized download via primary key -> 404
        res_download_pk = self.client2.get(f'/api/reports/{report_pk}/download')
        self.assertEqual(res_download_pk.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts unauthorized delete -> 404
        res_del = self.client2.delete(f'/api/reports/{report_id}')
        self.assertEqual(res_del.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts unauthorized delete via primary key -> 404
        res_del_pk = self.client2.delete(f'/api/reports/{report_pk}')
        self.assertEqual(res_del_pk.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 attempts unauthorized HTML and Markdown access -> 404
        res_html = self.client2.get(f'/api/reports/{report_id}/html')
        self.assertEqual(res_html.status_code, status.HTTP_404_NOT_FOUND)
        res_md = self.client2.get(f'/api/reports/{report_id}/markdown')
        self.assertEqual(res_md.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 lists reports -> must be empty
        res_list_user2 = self.client2.get('/api/reports')
        self.assertEqual(res_list_user2.status_code, status.HTTP_200_OK)
        user2_results = res_list_user2.json().get("results", res_list_user2.json())
        self.assertEqual(len(user2_results), 0)

        # User 1 CAN view, check status, and download their own report
        res_owner_view = self.client1.get(f'/api/reports/{report_id}')
        self.assertEqual(res_owner_view.status_code, status.HTTP_200_OK)

        res_owner_status = self.client1.get(f'/api/reports/{report_id}/status')
        self.assertEqual(res_owner_status.status_code, status.HTTP_200_OK)
        self.assertEqual(res_owner_status.json()["status"], "completed")

        res_owner_download = self.client1.get(f'/api/reports/{report_id}/download')
        self.assertEqual(res_owner_download.status_code, status.HTTP_200_OK)
        self.assertEqual(res_owner_download["Content-Type"], "application/pdf")
        self.assertIn("attachment", res_owner_download["Content-Disposition"])

    @patch('api.services.report_generator.fetch_company_data')
    def test_report_listing_filtering_and_pagination(self, mock_fetch):
        """User can list reports with pagination and filter by ticker and status."""
        mock_fetch.return_value = get_mock_company_data("GOOGL")

        self.client1.post('/api/reports', data={"ticker": "GOOGL"}, format="json")

        # Filter by ticker match
        res_googl = self.client1.get('/api/reports?ticker=GOOGL')
        self.assertEqual(res_googl.status_code, status.HTTP_200_OK)
        data = res_googl.json()
        results = data.get("results", data)
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["ticker"], "GOOGL")

        # Filter by non-existent ticker
        res_none = self.client1.get('/api/reports?ticker=NONEXISTENT')
        self.assertEqual(res_none.status_code, status.HTTP_200_OK)
        none_results = res_none.json().get("results", res_none.json())
        self.assertEqual(len(none_results), 0)

        # Filter by status
        res_completed = self.client1.get('/api/reports?status=completed')
        self.assertEqual(res_completed.status_code, status.HTTP_200_OK)
        completed_results = res_completed.json().get("results", res_completed.json())
        self.assertTrue(len(completed_results) >= 1)

    @patch('api.services.report_generator.fetch_company_data')
    def test_failed_generation_error_handling(self, mock_fetch):
        """When financial data retrieval fails, return 404 and record failure details."""
        mock_fetch.side_effect = FinancialDataError("Company profile for INVALID not found.")

        response = self.client1.post('/api/reports', data={"ticker": "INVALID"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.json())

        # Verify failed report records error details if DB record was created
        failed_reports = ResearchReport.objects.filter(user=self.user1, ticker="INVALID")
        if failed_reports.exists():
            rep = failed_reports.first()
            self.assertEqual(rep.status, "failed")
            self.assertTrue(rep.error_details)

    @patch('api.services.report_generator.fetch_company_data')
    def test_delete_report_cleanup(self, mock_fetch):
        """Deleting an owned report removes the DB record and cleans up the PDF file."""
        mock_fetch.return_value = get_mock_company_data("NVDA")

        res = self.client1.post('/api/reports', data={"ticker": "NVDA"}, format="json")
        report_id = res.json()["report_id"]
        report = ResearchReport.objects.get(report_id=report_id)
        file_path = report.private_file_path

        self.assertTrue(os.path.exists(file_path))

        # Delete report
        del_res = self.client1.delete(f'/api/reports/{report_id}')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        # Verify DB deletion
        self.assertFalse(ResearchReport.objects.filter(report_id=report_id).exists())

        # Verify disk cleanup
        self.assertFalse(os.path.exists(file_path))

    def test_subscription_status_endpoint(self):
        """Tests the actual backend subscription status retrieval for authenticated and guest users."""
        # Authenticated user
        res_auth = self.client1.get('/api/subscription/status')
        self.assertEqual(res_auth.status_code, status.HTTP_200_OK)
        data_auth = res_auth.json()
        self.assertTrue(data_auth["is_authenticated"])
        self.assertEqual(data_auth["username"], "analyst_alice")
        self.assertEqual(data_auth["tier"], "free")
        self.assertEqual(data_auth["payment_gateway_status"], "not_integrated")
        self.assertEqual(data_auth["limits"]["max_pdf_pages"], 50)

        # Anonymous user
        res_anon = self.anon_client.get('/api/subscription/status')
        self.assertEqual(res_anon.status_code, status.HTTP_200_OK)
        data_anon = res_anon.json()
        self.assertFalse(data_anon["is_authenticated"])
        self.assertEqual(data_anon["tier"], "guest")

    @patch('api.services.report_generator.fetch_company_data')
    def test_end_to_end_full_user_lifecycle(self, mock_fetch):
        """
        Complete End-to-End Workflow Verification:
        1. User authentication
        2. Financial data retrieval & metrics evaluation
        3. 15-section report generation with strict 50-page cap
        4. Programmatic PyPDF page verification and metadata check
        5. PostgreSQL persistence with authenticated user ownership
        6. My Reports listing and filtering
        7. PDF download with verified binary integrity
        8. Cross-user isolation (User B denied with 404)
        9. Cleanup on deletion (DB & file)
        """
        mock_fetch.return_value = get_mock_company_data("TCS")

        # 1. Initiate Report Generation
        gen_res = self.client1.post(
            '/api/reports/',
            data={"ticker": "TCS", "report_title": "Tata Consultancy Services Institutional Dossier"},
            format="json"
        )
        self.assertEqual(gen_res.status_code, status.HTTP_201_CREATED)
        report_data = gen_res.json()
        report_id = report_data["report_id"]

        # 2. Check Status Endpoint
        status_res = self.client1.get(f'/api/reports/{report_id}/status/')
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        self.assertEqual(status_res.json()["status"], "completed")
        self.assertLessEqual(status_res.json()["page_count"], 50)

        # 3. Verify PostgreSQL Persistence & Ownership
        report_obj = ResearchReport.objects.get(report_id=report_id)
        self.assertEqual(report_obj.user, self.user1)
        self.assertEqual(report_obj.ticker, "TCS")
        self.assertEqual(report_obj.sections.count(), 15)

        # 4. Verify Programmatic PDF Rendering and 50-Page Cap
        pdf_path = report_obj.private_file_path
        self.assertTrue(os.path.exists(pdf_path))
        reader = pypdf.PdfReader(pdf_path)
        page_count = len(reader.pages)
        self.assertLessEqual(page_count, 50)
        self.assertEqual(page_count, report_obj.page_count)

        # Verify Cover Page contains required metadata
        page1_text = reader.pages[0].extract_text()
        self.assertIn("INSTITUTIONAL", page1_text.upper())
        self.assertIn("TCS", page1_text.upper())

        # 5. Verify My Reports Listing (Authenticated User 1)
        list_res = self.client1.get('/api/reports/?ticker=TCS')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        my_reports = list_res.json().get("results", list_res.json())
        self.assertTrue(any(r["report_id"] == str(report_id) for r in my_reports))

        # 6. Verify PDF Download Binary Response
        download_res = self.client1.get(f'/api/reports/{report_id}/download/')
        self.assertEqual(download_res.status_code, status.HTTP_200_OK)
        self.assertEqual(download_res["Content-Type"], "application/pdf")
        self.assertIn("TCS_Institutional_Report.pdf", download_res["Content-Disposition"])
        # Verify PDF magic bytes
        pdf_content = b"".join(download_res.streaming_content)
        self.assertTrue(pdf_content.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_content), 1000)

        # 7. Verify Cross-User Isolation (User 2 blocked with 404)
        self.assertEqual(self.client2.get(f'/api/reports/{report_id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client2.get(f'/api/reports/{report_id}/status/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client2.get(f'/api/reports/{report_id}/download/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client2.delete(f'/api/reports/{report_id}/').status_code, status.HTTP_404_NOT_FOUND)

        # 8. Clean up
        del_res = self.client1.delete(f'/api/reports/{report_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ResearchReport.objects.filter(report_id=report_id).exists())
        self.assertFalse(os.path.exists(pdf_path))


class UserDashboardAndWatchlistTests(TestCase):
    """
    Tests for Prompt 6:
    - User Dashboard personalized endpoint
    - Saved Companies Watchlist CRUD and duplicate prevention
    - Watchlist and Research History cross-user isolation
    - Research activity logging and filtering
    - Authentication login, logout, and current user endpoints
    """
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="analyst_alice",
            email="alice@hedgefund.com",
            password="StrongPassword123!",
            first_name="Alice",
            last_name="Smith"
        )
        self.user2 = User.objects.create_user(
            username="analyst_bob",
            email="bob@hedgefund.com",
            password="StrongPassword456!",
            first_name="Bob",
            last_name="Jones"
        )
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.anon_client = APIClient()

    def test_dashboard_unauthenticated_blocked(self):
        res = self.anon_client.get('/api/dashboard/')
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_dashboard_authenticated_data(self):
        # Add some initial records for User 1
        SavedCompany.objects.create(
            user=self.user1,
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            notes="Long term core holding"
        )
        ResearchActivity.objects.create(
            user=self.user1,
            ticker="AAPL",
            company_name="Apple Inc.",
            research_type="quantitative",
            summary_data={"passed_count": 5, "failed_count": 0}
        )

        res = self.client1.get('/api/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()

        self.assertIn("welcome_message", data)
        self.assertIn("Alice", data["welcome_message"])
        self.assertEqual(data["stats"]["saved_companies_count"], 1)
        self.assertEqual(data["stats"]["activities_count"], 1)
        self.assertEqual(len(data["saved_companies"]), 1)
        self.assertEqual(data["saved_companies"][0]["ticker"], "AAPL")
        self.assertEqual(len(data["recent_activities"]), 1)
        self.assertIn("subscription", data)
        self.assertEqual(data["subscription"]["tier"], "free")

    def test_watchlist_crud_and_duplicate_prevention(self):
        # 1. Add company to watchlist
        add_res = self.client1.post(
            '/api/watchlist/',
            {
                "ticker": "msft",
                "company_name": "Microsoft Corporation",
                "sector": "Cloud & Software",
                "notes": "Monitor AI capital expenditures"
            },
            format="json"
        )
        self.assertEqual(add_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_res.json()["ticker"], "MSFT")

        # 2. Duplicate prevention
        dup_res = self.client1.post(
            '/api/watchlist/',
            {
                "ticker": "MSFT",
                "company_name": "Microsoft Corporation"
            },
            format="json"
        )
        self.assertEqual(dup_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already in your saved watchlist", dup_res.json()["detail"])

        # 3. Check endpoint
        check_res = self.client1.get('/api/watchlist/check/?ticker=MSFT')
        self.assertEqual(check_res.status_code, status.HTTP_200_OK)
        self.assertTrue(check_res.json()["is_saved"])

        # 4. List and search
        list_res = self.client1.get('/api/watchlist/?query=Micro')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.json()), 1)
        self.assertEqual(list_res.json()[0]["ticker"], "MSFT")

        # 5. Delete by ticker
        del_res = self.client1.delete('/api/watchlist/MSFT/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        # 6. Verify removed
        check_res_after = self.client1.get('/api/watchlist/check/?ticker=MSFT')
        self.assertFalse(check_res_after.json()["is_saved"])

    def test_watchlist_user_ownership_isolation(self):
        # User 1 saves NVDA
        SavedCompany.objects.create(
            user=self.user1,
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            sector="Semiconductors"
        )

        # User 2 checks watchlist -> NVDA must not be visible
        res_user2 = self.client2.get('/api/watchlist/')
        self.assertEqual(res_user2.status_code, status.HTTP_200_OK)
        tickers_user2 = [c["ticker"] for c in res_user2.json()]
        self.assertNotIn("NVDA", tickers_user2)

        # User 2 tries to delete User 1's NVDA -> returns 404
        del_attempt = self.client2.delete('/api/watchlist/NVDA/')
        self.assertEqual(del_attempt.status_code, status.HTTP_404_NOT_FOUND)

        # User 1's NVDA remains intact
        self.assertTrue(SavedCompany.objects.filter(user=self.user1, ticker="NVDA").exists())

    def test_research_history_logging_and_filtering(self):
        # Log qualitative activity for User 1
        act1_res = self.client1.post(
            '/api/history/',
            {
                "ticker": "TSLA",
                "company_name": "Tesla, Inc.",
                "research_type": "qualitative",
                "summary_data": {"notes": "Retrieved 10-K EV margins"}
            },
            format="json"
        )
        self.assertEqual(act1_res.status_code, status.HTTP_201_CREATED)
        act1_id = act1_res.json()["id"]

        # Log quantitative activity for User 1
        self.client1.post(
            '/api/history/',
            {
                "ticker": "TSLA",
                "company_name": "Tesla, Inc.",
                "research_type": "quantitative",
                "summary_data": {"passed_count": 3}
            },
            format="json"
        )

        # Query filter by research_type=qualitative
        filter_res = self.client1.get('/api/history/?research_type=qualitative')
        self.assertEqual(filter_res.status_code, status.HTTP_200_OK)
        results = filter_res.json().get("results", filter_res.json())
        self.assertTrue(all(item["research_type"] == "qualitative" for item in results))

        # User 2 cannot see User 1's history
        user2_history = self.client2.get('/api/history/')
        u2_results = user2_history.json().get("results", user2_history.json())
        self.assertEqual(len(u2_results), 0)

        # User 2 cannot access or delete User 1's activity
        self.assertEqual(self.client2.get(f'/api/history/{act1_id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client2.delete(f'/api/history/{act1_id}/').status_code, status.HTTP_404_NOT_FOUND)

        # User 1 can delete own activity
        self.assertEqual(self.client1.delete(f'/api/history/{act1_id}/').status_code, status.HTTP_204_NO_CONTENT)

    def test_auth_login_logout_user_endpoints(self):
        # 1. Login with bad credentials -> 401
        bad_login = self.anon_client.post(
            '/api/auth/login/',
            {"username": "analyst_alice", "password": "WrongPassword"},
            format="json"
        )
        self.assertEqual(bad_login.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Login with valid credentials -> 200 + token
        good_login = self.anon_client.post(
            '/api/auth/login/',
            {"username": "analyst_alice", "password": "StrongPassword123!"},
            format="json"
        )
        self.assertEqual(good_login.status_code, status.HTTP_200_OK)
        self.assertIn("token", good_login.json())
        token = good_login.json()["token"]

        # 3. Check AuthUserView using token
        token_client = APIClient()
        token_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        user_res = token_client.get('/api/auth/user/')
        self.assertEqual(user_res.status_code, status.HTTP_200_OK)
        self.assertTrue(user_res.json()["is_authenticated"])
        self.assertEqual(user_res.json()["user"]["username"], "analyst_alice")

        # 4. Logout
        logout_res = token_client.post('/api/auth/logout/')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

    def test_user_registration_success_and_password_hashing(self):
        """
        Verifies successful registration:
        - User is created in database.
        - Password is stored as a secure hash, NEVER in plain text.
        - Password hashes or credentials are never exposed in API response.
        - Token and user metadata are returned.
        """
        payload = {
            "username": "quantitative_trader",
            "password": "UltraSecurePassword999!",
            "confirm_password": "UltraSecurePassword999!",
        }
        res = self.anon_client.post('/api/auth/register/', data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        res_data = res.json()

        self.assertIn("message", res_data)
        self.assertIn("token", res_data)
        self.assertIn("user", res_data)
        self.assertEqual(res_data["user"]["username"], "quantitative_trader")

        # Verify password is never returned
        self.assertNotIn("password", res_data["user"])
        self.assertNotIn("password_hash", res_data["user"])

        # Verify PostgreSQL / DB record
        user = User.objects.get(username="quantitative_trader")
        self.assertTrue(user.check_password("UltraSecurePassword999!"))
        # Password must be hashed with PBKDF2/Argon2/BCrypt, not plain text
        self.assertNotEqual(user.password, "UltraSecurePassword999!")
        self.assertTrue(user.password.startswith("pbkdf2_") or user.password.startswith("argon2") or user.password.startswith("bcrypt"))

    def test_user_registration_duplicate_username_rejected(self):
        """Duplicate username must be rejected at API and database validation layers."""
        payload = {
            "username": "analyst_alice",  # Already exists from setUp
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.anon_client.post('/api/auth/register/', data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", str(res.json()))

    def test_user_registration_password_mismatch(self):
        """Mismatched passwords must be rejected with a clear validation error."""
        payload = {
            "username": "new_analyst_user",
            "password": "Password123!",
            "confirm_password": "DifferentPassword456!",
        }
        res = self.anon_client.post('/api/auth/register/', data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", res.json())
        self.assertIn("do not match", str(res.json()["confirm_password"]))

    def test_user_registration_validation_length_rules(self):
        """Short usernames (<3 chars) and short passwords (<6 chars) must be rejected."""
        # Short username
        res1 = self.anon_client.post('/api/auth/register/', {
            "username": "ab",
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        }, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # Short password
        res2 = self.anon_client.post('/api/auth/register/', {
            "username": "valid_user",
            "password": "123",
            "confirm_password": "123",
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_auth_lifecycle_register_login_dashboard_isolation(self):
        """
        Tests complete lifecycle:
        Register -> Login -> Fetch Dashboard -> Verify zero initial leaks from other users.
        """
        reg_res = self.anon_client.post('/api/auth/register/', {
            "username": "carol_hedge",
            "password": "CarolPassword789!",
            "confirm_password": "CarolPassword789!",
        }, format="json")
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)

        # Login with new credentials
        login_res = self.anon_client.post('/api/auth/login/', {
            "username": "carol_hedge",
            "password": "CarolPassword789!",
        }, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        token = login_res.json()["token"]

        # Authenticated dashboard access
        carol_client = APIClient()
        carol_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        dash_res = carol_client.get('/api/dashboard/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        dash_data = dash_res.json()

        # Strict isolation: Carol has 0 saved companies and 0 reports
        self.assertEqual(dash_data["stats"]["saved_companies_count"], 0)
        self.assertEqual(dash_data["stats"]["reports_count"], 0)
        self.assertEqual(len(dash_data["saved_companies"]), 0)


    @patch('research.analysis.get_llm_provider')
    @patch('api.services.report_generator.fetch_company_data')
    def test_report_generation_with_active_qualitative_rag(self, mock_fetch, mock_get_llm):
        """
        Verifies that report generation integrates both quantitative financials
        and active qualitative RAG document chunks into Section 12 and the final PDF.
        """
        mock_get_llm.return_value = MockLLMProvider()
        mock_fetch.return_value = get_mock_company_data("INFY")

        # 1. Seed Company, FinancialDocument, and DocumentChunk
        company = Company.objects.create(ticker="INFY", slug="infosys-ltd", name="Infosys Limited")
        doc = FinancialDocument.objects.create(
            company=company,
            external_id="uuid-infy-ar-2026",
            doc_type="annual_report",
            title="Infosys Annual Report 2026",
            fiscal_period="FY26",
            total_pages=360,
        )
        provider = DeterministicLocalEmbeddingProvider(dimension=128)
        content_text = (
            "MANAGEMENT DISCUSSION AND ANALYSIS - OPERATIONAL HIGHLIGHTS\n"
            "Operating margin expanded to 21.4% driven by Project Maximus operational efficiency, "
            "while large deal total contract value (TCV) reached $14.5 billion with 40% digital mix."
        )
        DocumentChunk.objects.create(
            document=doc,
            chunk_index=0,
            content=content_text,
            chunk_hash="sha256-infy-0",
            section_heading="Management Discussion and Analysis",
            page_start=45,
            page_end=46,
            char_count=len(content_text),
            word_count=len(content_text.split()),
            embedding_model=provider.model_name,
            embedding=provider.embed_texts([content_text])[0],
            metadata={"source": "annual_report"},
        )

        # 2. Run report generation
        generator = InstitutionalReportGenerator(ticker="INFY", user=self.user1)
        report = generator.generate()

        # 3. Verify report completion and page cap
        self.assertEqual(report.status, "completed")
        self.assertLessEqual(report.page_count, 50)
        self.assertTrue(os.path.exists(report.private_file_path))

        # 4. Verify Section 12 has qualitative evidence
        sec12 = report.sections.get(section_number=12)
        self.assertTrue(sec12.has_qualitative_evidence)
        self.assertGreater(len(sec12.citations), 0)

        # 5. Verify citations structure has document_title, fiscal_period, and page_range
        cite = sec12.citations[0]
        self.assertEqual(cite["document_title"], "Infosys Annual Report 2026")
        self.assertEqual(cite["fiscal_period"], "FY26")
        self.assertEqual(cite["page_range"], "pp. 45-46")

        # 6. Verify Section 12 markdown contains findings and citation attribution
        self.assertIn("Source Document Attribution:", sec12.content_markdown)
        self.assertIn("Infosys Annual Report 2026", sec12.content_markdown)
        self.assertIn("pp. 45-46", sec12.content_markdown)

        # 7. Verify rendered PDF contains verified document citations
        reader = pypdf.PdfReader(report.private_file_path)
        full_pdf_text = " ".join([page.extract_text() or "" for page in reader.pages])
        self.assertIn("Verified Document Citations:", full_pdf_text)
        self.assertIn("Infosys Annual Report 2026", full_pdf_text)


