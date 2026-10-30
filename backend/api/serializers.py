from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import InvestmentPrinciple, ResearchReport, ReportSection, SavedCompany, ResearchActivity

User = get_user_model()

class InvestmentPrincipleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentPrinciple
        fields = ['identifier', 'name', 'metric', 'operator', 'threshold', 'description']

class PrincipleUpdateSerializer(serializers.Serializer):
    threshold = serializers.FloatField(required=True)

class AnalyzeRequestSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=32, required=True)

class AskRequestSerializer(serializers.Serializer):
    question = serializers.CharField(required=True)
    context = serializers.DictField(required=True)

class CompareRequestSerializer(serializers.Serializer):
    tickers = serializers.ListField(
        child=serializers.CharField(max_length=32),
        min_length=2,
        max_length=2,
        required=True
    )

class ReportSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSection
        fields = [
            'section_number',
            'section_key',
            'title',
            'page_count',
            'content_markdown',
            'structured_data',
            'has_qualitative_evidence',
            'citations',
        ]

class ResearchReportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchReport
        fields = [
            'id',
            'report_id',
            'ticker',
            'company_name',
            'report_title',
            'report_type',
            'status',
            'page_count',
            'page_limit',
            'conviction_rating',
            'principles_pass_rate_pct',
            'generation_date',
        ]

class ResearchReportDetailSerializer(serializers.ModelSerializer):
    sections = ReportSectionSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchReport
        fields = [
            'id',
            'report_id',
            'ticker',
            'company_name',
            'report_title',
            'report_type',
            'status',
            'page_count',
            'page_limit',
            'execution_time_seconds',
            'error_details',
            'conviction_rating',
            'principles_pass_rate_pct',
            'principles_passed_count',
            'principles_total_count',
            'research_snapshot',
            'markdown_content',
            'sections',
            'generation_date',
            'updated_at',
        ]

class GenerateReportRequestSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=32, required=True)
    report_title = serializers.CharField(max_length=255, required=False, allow_blank=True)


class SavedCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedCompany
        fields = [
            'id',
            'ticker',
            'company_name',
            'sector',
            'notes',
            'added_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']


class SavedCompanyCreateSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=50, required=True)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    sector = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ResearchActivitySerializer(serializers.ModelSerializer):
    report_id = serializers.UUIDField(source='report.report_id', read_only=True)

    class Meta:
        model = ResearchActivity
        fields = [
            'id',
            'ticker',
            'company_name',
            'research_type',
            'status',
            'summary_data',
            'report_id',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=150,
        trim_whitespace=True,
        error_messages={
            "required": "Username is required.",
            "blank": "Username cannot be empty.",
            "min_length": "Username must be at least 3 characters long.",
        }
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        error_messages={
            "required": "Password is required.",
            "blank": "Password cannot be empty.",
            "min_length": "Password must be at least 6 characters long.",
        }
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        error_messages={
            "required": "Please confirm your password.",
            "blank": "Please confirm your password.",
        }
    )

    def validate_username(self, value):
        clean_username = value.strip()
        if User.objects.filter(username__iexact=clean_username).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return clean_username

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]
        # Creates user with secure PBKDF2-SHA256 hashed password using Django's password hashing
        user = User.objects.create_user(username=username, password=password)
        return user

