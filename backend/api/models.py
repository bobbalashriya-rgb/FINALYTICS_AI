import enum
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()

class Operator(str, enum.Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="

class InvestmentPrinciple(models.Model):
    OPERATOR_CHOICES = [
        (Operator.GREATER_THAN.value, ">"),
        (Operator.LESS_THAN.value, "<"),
        (Operator.GREATER_THAN_OR_EQUAL.value, ">="),
        (Operator.LESS_THAN_OR_EQUAL.value, "<="),
    ]

    identifier = models.CharField(max_length=64, primary_key=True, help_text="Unique principle identifier")
    name = models.CharField(max_length=255, help_text="Human-readable rule name")
    metric = models.CharField(max_length=100, help_text="Target metric identifier")
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, help_text="Evaluation operator")
    threshold = models.FloatField(help_text="Numeric threshold hurdle")
    description = models.TextField(help_text="Detailed principle rationale")

    class Meta:
        db_table = "investment_principles"
        ordering = ["identifier"]
        verbose_name = "Investment Principle"
        verbose_name_plural = "Investment Principles"

    def __str__(self):
        return f"{self.name} ({self.metric} {self.operator} {self.threshold})"


class ResearchReport(models.Model):
    """
    Persistent Institutional Investment Research Dossier generated for a specific company.
    Strictly isolated per authenticated user and constrained to a maximum of 50 PDF pages.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    report_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="research_reports",
        help_text="Authenticated user who requested and owns this report",
    )
    ticker = models.CharField(max_length=20, db_index=True)
    company_name = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    report_title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=64, default="institutional_equity_research")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    
    # Private storage location (not exposed via public static URLs)
    private_file_path = models.CharField(max_length=500, blank=True, null=True)
    page_count = models.PositiveIntegerField(default=1)
    page_limit = models.PositiveIntegerField(default=50)
    generation_date = models.DateTimeField(auto_now_add=True, db_index=True)
    execution_time_seconds = models.FloatField(null=True, blank=True)
    error_details = models.TextField(blank=True, null=True)

    # Core high-level ratings
    conviction_rating = models.CharField(max_length=100, blank=True, null=True)
    principles_pass_rate_pct = models.FloatField(null=True, blank=True)
    principles_passed_count = models.PositiveSmallIntegerField(default=0)
    principles_total_count = models.PositiveSmallIntegerField(default=0)

    # Research Input Snapshots (ensures reproducibility)
    research_snapshot = models.JSONField(default=dict, help_text="Reproducible snapshot of all quantitative & qualitative inputs")
    markdown_content = models.TextField(blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "company_research_reports"
        ordering = ["-generation_date"]
        indexes = [
            models.Index(fields=["user", "-generation_date"]),
            models.Index(fields=["ticker", "-generation_date"]),
            models.Index(fields=["report_id"]),
        ]

    def __str__(self):
        return f"{self.ticker} Report ({self.report_id}) - {self.status}"


# Backward compatibility alias
CompanyResearchReport = ResearchReport


class ReportSection(models.Model):
    """
    Individual section within the 15-part research report dossier.
    """
    report = models.ForeignKey(
        ResearchReport,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    section_number = models.PositiveSmallIntegerField(help_text="1 to 15")
    section_key = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    page_count = models.PositiveSmallIntegerField(default=1)

    content_markdown = models.TextField(blank=True, default="")
    structured_data = models.JSONField(default=dict)

    has_qualitative_evidence = models.BooleanField(default=False)
    citations = models.JSONField(default=list)

    class Meta:
        db_table = "report_sections"
        ordering = ["report", "section_number"]
        constraints = [
            models.UniqueConstraint(fields=["report", "section_number"], name="unique_report_section_num")
        ]

    def __str__(self):
        return f"Section {self.section_number}: {self.title} ({self.report.ticker})"


class SavedCompany(models.Model):
    """
    Watchlist of companies saved by an authenticated user for ongoing research,
    valuation tracking, and quick report generation.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_companies",
        help_text="User who saved this company to their watchlist",
    )
    ticker = models.CharField(max_length=50, db_index=True)
    company_name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saved_companies"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "ticker"],
                name="unique_user_saved_company",
            )
        ]
        indexes = [
            models.Index(fields=["user", "-added_at"]),
            models.Index(fields=["user", "ticker"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.ticker}"


class ResearchActivity(models.Model):
    """
    Audit log of quantitative, qualitative, and report research sessions conducted
    by authenticated users. Enables historical replay without rerunning heavy pipeline jobs.
    """
    RESEARCH_TYPE_CHOICES = [
        ("quantitative", "Quantitative Analysis"),
        ("qualitative", "Qualitative Research"),
        ("report", "Research Report"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="research_activities",
        help_text="User who conducted this research session",
    )
    ticker = models.CharField(max_length=50, db_index=True)
    company_name = models.CharField(max_length=255)
    research_type = models.CharField(max_length=30, choices=RESEARCH_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, default="completed", db_index=True)
    summary_data = models.JSONField(default=dict, blank=True)
    report = models.ForeignKey(
        ResearchReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "research_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "research_type"]),
            models.Index(fields=["user", "ticker"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.research_type} on {self.ticker} ({self.created_at.strftime('%Y-%m-%d')})"
