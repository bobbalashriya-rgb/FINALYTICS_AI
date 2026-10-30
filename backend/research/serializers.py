from rest_framework import serializers


class EvidenceItemSerializer(serializers.Serializer):
    """
    Schema for an individual evidence chunk retrieved from financial reports.
    """
    chunk_id = serializers.IntegerField(help_text="Database ID of the chunk")
    chunk_index = serializers.IntegerField(help_text="Sequential index of chunk in document")
    document_id = serializers.IntegerField(help_text="Local database document ID")
    document_external_id = serializers.CharField(help_text="MarketPing document UUID")
    document_title = serializers.CharField(help_text="Document title")
    document_type = serializers.CharField(help_text="Type of document (e.g. annual_report)")
    fiscal_period = serializers.CharField(allow_null=True, help_text="e.g. FY26 or FY27 Q1")
    period_end_date = serializers.CharField(allow_null=True, help_text="Reporting period end date")
    section_heading = serializers.CharField(help_text="Detected section or heading")
    page_start = serializers.IntegerField(help_text="First page containing the passage")
    page_end = serializers.IntegerField(help_text="Last page containing the passage")
    content = serializers.CharField(help_text="Extracted report text")
    relevance_score = serializers.FloatField(help_text="Overall hybrid relevance score (0.0 - 1.0)")
    semantic_similarity = serializers.FloatField(help_text="Vector cosine similarity score (0.0 - 1.0)")
    keyword_matches = serializers.ListField(
        child=serializers.CharField(),
        help_text="Matched keywords from the research query",
    )
    source_reference = serializers.CharField(
        allow_null=True,
        required=False,
        help_text="Original MarketPing source link or reference",
    )


class EvidenceRetrieveRequestSerializer(serializers.Serializer):
    """
    Request payload parameters for retrieving research evidence.
    """
    ticker = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Company ticker symbol or name (e.g. INFY, TCS, RELIANCE)",
    )
    question = serializers.CharField(
        min_length=3,
        max_length=1000,
        required=True,
        help_text="The qualitative research question or topic to search for",
    )
    document_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Optional list of document types to filter (e.g. ['annual_report', 'earnings_call_transcript'])",
    )
    fiscal_periods = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Optional list of fiscal periods to filter (e.g. ['FY26', 'FY25'])",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=25,
        help_text="Maximum number of relevant evidence passages to return (default: 5, max: 25)",
    )
    min_score = serializers.FloatField(
        required=False,
        default=0.15,
        min_value=0.0,
        max_value=1.0,
        help_text="Minimum relevance threshold to filter noisy results (default: 0.15)",
    )


class EvidenceRetrieveResponseSerializer(serializers.Serializer):
    """
    Response schema for the evidence retrieval endpoint.
    """
    ticker = serializers.CharField()
    company_name = serializers.CharField()
    question = serializers.CharField()
    total_chunks_searched = serializers.IntegerField()
    total_evidence_found = serializers.IntegerField()
    has_evidence = serializers.BooleanField()
    message = serializers.CharField()
    evidence = EvidenceItemSerializer(many=True)


class CitationItemSerializer(serializers.Serializer):
    """
    Schema for a verified evidence citation.
    """
    chunk_id = serializers.IntegerField()
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    document_type = serializers.CharField()
    fiscal_period = serializers.CharField(allow_null=True)
    page_start = serializers.IntegerField()
    page_end = serializers.IntegerField()
    section_heading = serializers.CharField()
    source_reference = serializers.CharField(allow_null=True, required=False)


class FindingItemSerializer(serializers.Serializer):
    """
    Schema for an epistemic finding categorized as fact, statement, or interpretation.
    """
    claim = serializers.CharField()
    category = serializers.ChoiceField(
        choices=["reported_fact", "management_statement", "analytical_interpretation"]
    )
    chunk_ids = serializers.ListField(child=serializers.IntegerField())
    quote = serializers.CharField(allow_blank=True, required=False)


class QualitativeAnalysisRequestSerializer(serializers.Serializer):
    """
    Request parameters for generating evidence-grounded fundamental analysis.
    """
    ticker = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Company ticker symbol or name (e.g. INFY, TCS, RELIANCE)",
    )
    question = serializers.CharField(
        min_length=3,
        max_length=1000,
        required=True,
        help_text="Qualitative research question to analyze",
    )
    document_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Optional document types to filter (e.g. ['annual_report'])",
    )
    fiscal_periods = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Optional fiscal periods to filter (e.g. ['FY26'])",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=8,
        min_value=1,
        max_value=25,
        help_text="Max evidence passages to retrieve for LLM analysis (default: 8)",
    )
    min_score = serializers.FloatField(
        required=False,
        default=0.15,
        min_value=0.0,
        max_value=1.0,
        help_text="Relevance threshold for retrieved evidence (default: 0.15)",
    )


class QualitativeAnalysisResponseSerializer(serializers.Serializer):
    """
    Structured response schema for evidence-grounded qualitative fundamental analysis.
    """
    company = serializers.DictField()
    question = serializers.CharField()
    executive_summary = serializers.CharField()
    key_findings = FindingItemSerializer(many=True)
    citations = CitationItemSerializer(many=True)
    risks_and_uncertainties = serializers.ListField(child=serializers.CharField())
    missing_information_and_limitations = serializers.ListField(child=serializers.CharField())
    prompt_version = serializers.CharField()
    model_name = serializers.CharField()
    has_sufficient_evidence = serializers.BooleanField()
    total_evidence_chunks_evaluated = serializers.IntegerField()
    metrics = serializers.DictField(required=False)


class ResearchEvaluationResponseSerializer(serializers.Serializer):
    """
    Response schema combining full qualitative analysis with formal evaluation scores.
    """
    analysis = QualitativeAnalysisResponseSerializer()
    evaluation = serializers.DictField()
