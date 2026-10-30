from django.apps import AppConfig
from django.db.models.signals import post_migrate

DEFAULT_PRINCIPLES = [
    {
        "identifier": "ROE_GT_15", 
        "name": "High Return on Equity", 
        "metric": "roe", 
        "operator": ">", 
        "threshold": 0.15, 
        "description": "Checks if Return on Equity is strictly greater than 15%."
    },
    {
        "identifier": "DEBT_EQ_LT_05", 
        "name": "Low Debt to Equity", 
        "metric": "debt_to_equity", 
        "operator": "<", 
        "threshold": 0.5, 
        "description": "Checks if Debt to Equity ratio is less than 0.5."
    },
    {
        "identifier": "REV_GROWTH_GT_10", 
        "name": "Strong Revenue Growth", 
        "metric": "revenue_growth", 
        "operator": ">", 
        "threshold": 0.10, 
        "description": "Checks if year-over-year revenue growth is greater than 10%."
    },
    {
        "identifier": "OP_MARGIN_GT_15", 
        "name": "Healthy Operating Margin", 
        "metric": "operating_margin", 
        "operator": ">", 
        "threshold": 0.15, 
        "description": "Checks if the operating margin is greater than 15%."
    },
    {
        "identifier": "FCF_POSITIVE", 
        "name": "Positive Free Cash Flow", 
        "metric": "free_cash_flow", 
        "operator": ">", 
        "threshold": 0.0, 
        "description": "Checks if the free cash flow is strictly positive."
    },
    {
        "identifier": "PE_LT_30", 
        "name": "Reasonable Valuation (P/E)", 
        "metric": "pe_ratio", 
        "operator": "<", 
        "threshold": 30.0, 
        "description": "Checks if the Price to Earnings ratio is less than 30."
    }
]

def seed_default_principles(sender, **kwargs):
    from .models import InvestmentPrinciple
    try:
        if InvestmentPrinciple.objects.count() == 0:
            for p in DEFAULT_PRINCIPLES:
                InvestmentPrinciple.objects.create(**p)
            print("[INFO] Seeded default investment principles.")
    except Exception as e:
        # Avoid crashing during migrations before table exists
        pass

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        post_migrate.connect(seed_default_principles, sender=self)

