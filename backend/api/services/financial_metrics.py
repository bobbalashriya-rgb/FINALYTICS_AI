import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from .company_data import NormalizedCompanyData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Output Models
# ---------------------------------------------------------

class HistoricalMetric(BaseModel):
    date: str
    revenue: Optional[float]
    net_profit: Optional[float]
    operating_margin: Optional[float]

class ValuationMetricItem(BaseModel):
    key: str
    abbreviation: str
    name: str
    value: Optional[float] = None
    formatted_value: str
    unit: str = "ratio"  # "ratio", "currency", "percentage"
    formula: str
    explanation: str
    interpretation: str
    source: str = "Yahoo Finance & Financial Statements"

class EarningsValuation(BaseModel):
    pe: ValuationMetricItem
    forward_pe: ValuationMetricItem
    peg: ValuationMetricItem
    ps: ValuationMetricItem
    pb: ValuationMetricItem
    ev_ebitda: ValuationMetricItem
    ev_ebit: ValuationMetricItem
    ev_sales: ValuationMetricItem
    description: str = "Core earnings and enterprise multiples comparing market price against reported and forward earning power."

class GrowthValuation(BaseModel):
    peg_ratio: ValuationMetricItem
    rule_of_40: ValuationMetricItem
    price_to_fcf: ValuationMetricItem
    fcf_growth: ValuationMetricItem
    profit_growth: ValuationMetricItem
    description: str = "Evaluates whether current valuation multiples are justified by the business's underlying growth rate."

class HistoricalValuationPoint(BaseModel):
    date: str
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    estimated_pe: Optional[float] = None

class HistoricalValuation(BaseModel):
    history: List[HistoricalValuationPoint] = []
    avg_pe: Optional[float] = None
    current_vs_avg_pe_pct: Optional[float] = None
    description: str = "Multi-year trend analysis showing how valuation multiples and profit margins evolved across reported financial statements."

class RelativeValuation(BaseModel):
    sector: Optional[str] = None
    industry: Optional[str] = None
    stock_pe: Optional[float] = None
    benchmark_pe: Optional[float] = None
    pe_discount_premium_pct: Optional[float] = None
    stock_pb: Optional[float] = None
    benchmark_pb: Optional[float] = None
    stock_ev_ebitda: Optional[float] = None
    benchmark_ev_ebitda: Optional[float] = None
    status_badge: str
    description: str = "Benchmarking stock multiples against sector peers to assess relative valuation premiums or discounts."

class DCFAssumptions(BaseModel):
    base_fcf: Optional[float] = None
    growth_rate_pct: float = 10.0
    discount_rate_pct: float = 10.5
    terminal_growth_rate_pct: float = 3.0
    forecast_years: int = 5
    net_debt: Optional[float] = None
    shares_outstanding: Optional[int] = None

class DCFValuation(BaseModel):
    is_available: bool
    reason: Optional[str] = None
    assumptions: DCFAssumptions
    projected_fcf: List[Dict[str, Any]] = []
    terminal_value: Optional[float] = None
    present_value_terminal: Optional[float] = None
    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    intrinsic_value_per_share: Optional[float] = None
    current_price: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    description: str = "Intrinsic valuation model calculating fair value by discounting projected future Free Cash Flows to present value."

class ValuationQualityRisk(BaseModel):
    interest_coverage: ValuationMetricItem
    debt_to_equity: ValuationMetricItem
    cash_conversion: ValuationMetricItem
    beta: ValuationMetricItem
    overall_risk_badge: str
    description: str = "Assesses balance sheet solvency, financial leverage, and the cash backing behind reported net income."

class ValuationModules(BaseModel):
    earnings_valuation: EarningsValuation
    growth_valuation: GrowthValuation
    historical_valuation: HistoricalValuation
    relative_valuation: RelativeValuation
    dcf_valuation: DCFValuation
    quality_risk: ValuationQualityRisk

class CalculatedMetrics(BaseModel):
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    net_profit: Optional[float] = None
    profit_growth: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    debt_to_equity: Optional[float] = None
    operating_margin: Optional[float] = None
    free_cash_flow: Optional[float] = None
    pe_ratio: Optional[float] = None
    # 8 Earnings-Based Valuation fields on root metrics
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_ebit: Optional[float] = None
    ev_to_sales: Optional[float] = None

class FinancialMetricsResult(BaseModel):
    metrics: CalculatedMetrics
    historical_data: List[HistoricalMetric]
    valuation: Optional[ValuationModules] = None

# ---------------------------------------------------------
# Service Helpers
# ---------------------------------------------------------

def _get_val(data_dict: Dict[str, Any], date_key: str, possible_keys: List[str]) -> Optional[float]:
    """
    Helper to extract a metric from a specific date's dictionary using possible key variations.
    Returns None if the data is unavailable or cannot be parsed.
    """
    if not data_dict or date_key not in data_dict:
        return None
        
    period_data = data_dict[date_key]
    for key in possible_keys:
        if key in period_data and period_data[key] is not None:
            try:
                return float(period_data[key])
            except (ValueError, TypeError):
                pass
    return None

def _format_val(val: Optional[float], unit: str = "ratio", currency: str = "USD") -> str:
    """Formats numeric values clearly or returns 'Not available'."""
    if val is None or (isinstance(val, float) and (val != val)):  # check None or NaN
        return "Not available"
    
    if unit == "ratio":
        return f"{val:.2f}x"
    elif unit == "percentage":
        # If fraction e.g. 0.15, format as 15.00%
        pct_val = val * 100 if abs(val) < 3.0 else val
        return f"{pct_val:.2f}%"
    elif unit == "currency":
        sym = "Γé╣" if currency == "INR" else "$"
        abs_v = abs(val)
        if currency == "INR":
            if abs_v >= 1e7:
                return f"{sym}{val / 1e7:.2f} Cr"
            elif abs_v >= 1e5:
                return f"{sym}{val / 1e5:.2f} Lakh"
        if abs_v >= 1e12:
            return f"{sym}{val / 1e12:.2f}T"
        elif abs_v >= 1e9:
            return f"{sym}{val / 1e9:.2f}B"
        elif abs_v >= 1e6:
            return f"{sym}{val / 1e6:.2f}M"
        return f"{sym}{val:,.2f}"
    return f"{val:.2f}"

# Sector Benchmarks for Relative Valuation
SECTOR_BENCHMARKS = {
    "Technology": {"pe": 28.5, "pb": 5.8, "ev_ebitda": 19.0},
    "Financial Services": {"pe": 14.5, "pb": 1.4, "ev_ebitda": 11.5},
    "Healthcare": {"pe": 24.0, "pb": 4.2, "ev_ebitda": 15.0},
    "Consumer Cyclical": {"pe": 22.0, "pb": 3.8, "ev_ebitda": 13.5},
    "Consumer Defensive": {"pe": 21.0, "pb": 3.5, "ev_ebitda": 14.0},
    "Industrials": {"pe": 20.5, "pb": 3.2, "ev_ebitda": 12.8},
    "Communication Services": {"pe": 19.5, "pb": 2.9, "ev_ebitda": 11.0},
    "Energy": {"pe": 12.0, "pb": 1.6, "ev_ebitda": 6.8},
    "Basic Materials": {"pe": 15.0, "pb": 2.1, "ev_ebitda": 8.5},
    "Utilities": {"pe": 16.5, "pb": 1.8, "ev_ebitda": 10.5},
    "Real Estate": {"pe": 25.0, "pb": 2.2, "ev_ebitda": 16.0},
}
DEFAULT_SECTOR_BENCHMARK = {"pe": 20.0, "pb": 3.0, "ev_ebitda": 13.0}

def calculate_metrics(data: NormalizedCompanyData) -> FinancialMetricsResult:
    """
    Calculates derived financial metrics and comprehensive 6-module quantitative valuation.
    Missing inputs result in safe None / 'Not available' values rather than fabricated estimates.
    """
    logger.info(f"Calculating metrics and valuation modules for {data.profile.ticker}")
    
    inc_stmt = data.financials.income_statement
    bal_sheet = data.financials.balance_sheet
    cash_flw = data.financials.cash_flow
    profile = data.profile
    ticker = profile.ticker.upper()
    currency = profile.currency or ("INR" if ticker.endswith(('.NS', '.BO')) else "USD")
    curr_sym = "Γé╣" if currency == "INR" else "$"

    dates_desc = sorted(list(inc_stmt.keys()), reverse=True)
    
    # --- 1. Source Data Extraction (Most Recent Period) ---
    recent_date = dates_desc[0] if dates_desc else None
    prev_date = dates_desc[1] if len(dates_desc) > 1 else None

    revenue = _get_val(inc_stmt, recent_date, ['Total Revenue', 'Operating Revenue']) if recent_date else None
    prev_revenue = _get_val(inc_stmt, prev_date, ['Total Revenue', 'Operating Revenue']) if prev_date else None
    
    net_profit = _get_val(inc_stmt, recent_date, ['Net Income', 'Net Income Common Stockholders']) if recent_date else None
    prev_net_profit = _get_val(inc_stmt, prev_date, ['Net Income', 'Net Income Common Stockholders']) if prev_date else None
    
    ebit = _get_val(inc_stmt, recent_date, ['EBIT', 'Operating Income']) if recent_date else None
    operating_income = _get_val(inc_stmt, recent_date, ['Operating Income', 'EBIT']) if recent_date else None
    ebitda = _get_val(inc_stmt, recent_date, ['EBITDA', 'Normalized EBITDA']) if recent_date else None
    interest_expense = _get_val(inc_stmt, recent_date, ['Interest Expense', 'Interest Expense Non Operating']) if recent_date else None

    # Balance Sheet Items
    equity = _get_val(bal_sheet, recent_date, ['Stockholders Equity', 'Total Stockholder Equity']) if recent_date else None
    total_assets = _get_val(bal_sheet, recent_date, ['Total Assets']) if recent_date else None
    current_liab = _get_val(bal_sheet, recent_date, ['Current Liabilities', 'Total Current Liabilities']) if recent_date else None
    total_debt = _get_val(bal_sheet, recent_date, ['Total Debt']) if recent_date else None
    cash = _get_val(bal_sheet, recent_date, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments']) if recent_date else None

    # Cash Flow Items
    ocf = _get_val(cash_flw, recent_date, ['Operating Cash Flow', 'Cash Flow From Continuing Operating Activities']) if recent_date else None
    prev_ocf = _get_val(cash_flw, prev_date, ['Operating Cash Flow', 'Cash Flow From Continuing Operating Activities']) if prev_date else None
    capex = _get_val(cash_flw, recent_date, ['Capital Expenditure']) if recent_date else None
    prev_capex = _get_val(cash_flw, prev_date, ['Capital Expenditure']) if prev_date else None

    # --- 2. Core Metrics ---
    market_cap = profile.market_cap
    enterprise_value = profile.enterprise_value or (
        (market_cap + (total_debt or 0) - (cash or 0)) if market_cap is not None else None
    )

    revenue_growth = None
    if revenue is not None and prev_revenue:
        revenue_growth = (revenue - prev_revenue) / abs(prev_revenue)
        
    profit_growth = None
    if net_profit is not None and prev_net_profit:
        profit_growth = (net_profit - prev_net_profit) / abs(prev_net_profit)

    roe = None
    if net_profit is not None and equity:
        roe = net_profit / equity
        
    roce = None
    if ebit is not None and total_assets is not None and current_liab is not None:
        capital_employed = total_assets - current_liab
        if capital_employed != 0:
            roce = ebit / capital_employed
            
    debt_to_equity = None
    if total_debt is not None and equity and equity > 0:
        debt_to_equity = total_debt / equity
        
    operating_margin = None
    if operating_income is not None and revenue and revenue > 0:
        operating_margin = operating_income / revenue

    free_cash_flow = None
    if ocf is not None and capex is not None:
        free_cash_flow = ocf - abs(capex)

    prev_fcf = None
    if prev_ocf is not None and prev_capex is not None:
        prev_fcf = prev_ocf - abs(prev_capex)

    fcf_growth = None
    if free_cash_flow is not None and prev_fcf and prev_fcf > 0:
        fcf_growth = (free_cash_flow - prev_fcf) / abs(prev_fcf)

    # --- 3. Eight Earnings-Based Valuation Multiples ---
    
    # 1. P/E
    pe_ratio = profile.trailing_pe
    if pe_ratio is None and market_cap is not None and net_profit and net_profit > 0:
        pe_ratio = market_cap / net_profit

    # 2. Forward P/E
    forward_pe = profile.forward_pe if (profile.forward_pe and profile.forward_pe > 0) else None

    # 3. PEG
    peg_ratio = profile.peg_ratio
    if peg_ratio is None and pe_ratio is not None and profit_growth and profit_growth > 0:
        peg_ratio = pe_ratio / (profit_growth * 100)

    # 4. P/S
    ps_ratio = profile.price_to_sales
    if ps_ratio is None and market_cap is not None and revenue and revenue > 0:
        ps_ratio = market_cap / revenue

    # 5. P/B
    pb_ratio = profile.price_to_book
    if pb_ratio is None and market_cap is not None and equity and equity > 0:
        pb_ratio = market_cap / equity

    # 6. EV/EBITDA
    ev_to_ebitda = profile.ev_to_ebitda
    if ev_to_ebitda is None and enterprise_value is not None and ebitda and ebitda > 0:
        ev_to_ebitda = enterprise_value / ebitda

    # 7. EV/EBIT
    ev_to_ebit = None
    if enterprise_value is not None and ebit and ebit > 0:
        ev_to_ebit = enterprise_value / ebit

    # 8. EV/Sales
    ev_to_sales = profile.ev_to_revenue
    if ev_to_sales is None and enterprise_value is not None and revenue and revenue > 0:
        ev_to_sales = enterprise_value / revenue

    # Construct Module 1: Earnings-Based Valuation
    earnings_val = EarningsValuation(
        pe=ValuationMetricItem(
            key="pe",
            abbreviation="P/E",
            name="Price-to-Earnings Ratio",
            value=pe_ratio,
            formatted_value=_format_val(pe_ratio, "ratio", currency),
            unit="ratio",
            formula="Share Price ├╖ Earnings Per Share (or Market Capitalization ├╖ Net Profit)",
            explanation=f"Shows how much investors pay for every {curr_sym}1 of annual earnings.",
            interpretation="A higher P/E does not automatically mean a stock is overvalued; compare it with similar companies and expected growth."
        ),
        forward_pe=ValuationMetricItem(
            key="forward_pe",
            abbreviation="Forward P/E",
            name="Forward Price-to-Earnings Ratio",
            value=forward_pe,
            formatted_value=_format_val(forward_pe, "ratio", currency),
            unit="ratio",
            formula="Current Share Price ├╖ Estimated Future EPS (Next 12 Months)",
            explanation=f"Estimates the valuation multiple based on consensus forward earnings forecasts over the upcoming year.",
            interpretation="A Forward P/E significantly lower than Trailing P/E indicates analysts project strong profit expansion ahead. Marked Not available if forward earnings are negative or unforecasted."
        ),
        peg=ValuationMetricItem(
            key="peg",
            abbreviation="PEG",
            name="Price/Earnings-to-Growth Ratio",
            value=peg_ratio,
            formatted_value=_format_val(peg_ratio, "ratio", currency),
            unit="ratio",
            formula="P/E Ratio ├╖ Annual Earnings Growth Rate (%)",
            explanation="Normalizes the standard P/E multiple by factoring in the company's expected earnings growth rate.",
            interpretation="A PEG below 1.0 is conventionally considered attractive valuation relative to growth; PEG around 1.0-1.5 is fairly valued; PEG well above 2.0 indicates investors are paying a steep premium for future growth."
        ),
        ps=ValuationMetricItem(
            key="ps",
            abbreviation="P/S",
            name="Price-to-Sales Ratio",
            value=ps_ratio,
            formatted_value=_format_val(ps_ratio, "ratio", currency),
            unit="ratio",
            formula="Market Capitalization ├╖ Total Annual Revenue",
            explanation=f"Measures the price investors pay for each {curr_sym}1 of top-line revenue generated by the business.",
            interpretation="Invaluable for evaluating cyclical businesses or fast-growing early-stage firms with thin or temporarily negative net margins."
        ),
        pb=ValuationMetricItem(
            key="pb",
            abbreviation="P/B",
            name="Price-to-Book Ratio",
            value=pb_ratio,
            formatted_value=_format_val(pb_ratio, "ratio", currency),
            unit="ratio",
            formula="Market Capitalization ├╖ Total Stockholders' Equity",
            explanation="Compares the firm's total market value against its net asset value (book equity recorded on the balance sheet).",
            interpretation="A P/B below 1.0 suggests the stock trades below balance sheet break-up value. Asset-light tech firms naturally trade at higher P/B multiples than capital-heavy banks or industrial manufacturers."
        ),
        ev_ebitda=ValuationMetricItem(
            key="ev_ebitda",
            abbreviation="EV/EBITDA",
            name="Enterprise Value to EBITDA",
            value=ev_to_ebitda,
            formatted_value=_format_val(ev_to_ebitda, "ratio", currency),
            unit="ratio",
            formula="Enterprise Value (Market Cap + Total Debt - Cash) ├╖ EBITDA",
            explanation="Compares the total takeover value of the enterprise (debt included, cash deducted) against operating cash flow before non-cash depreciation and amortization.",
            interpretation="Capital structure-neutral multiple widely used by institutional acquirers because it removes distortions from different debt levels and depreciation accounting methods."
        ),
        ev_ebit=ValuationMetricItem(
            key="ev_ebit",
            abbreviation="EV/EBIT",
            name="Enterprise Value to EBIT",
            value=ev_to_ebit,
            formatted_value=_format_val(ev_to_ebit, "ratio", currency),
            unit="ratio",
            formula="Enterprise Value ├╖ Operating Profit (EBIT)",
            explanation="Similar to EV/EBITDA, but includes capital depreciation and amortization, showing true core operational earning power after maintaining capital equipment.",
            interpretation="Offers a cleaner operational comparison than EV/EBITDA for asset-heavy businesses with real ongoing equipment replacement costs."
        ),
        ev_sales=ValuationMetricItem(
            key="ev_sales",
            abbreviation="EV/Sales",
            name="Enterprise Value to Sales",
            value=ev_to_sales,
            formatted_value=_format_val(ev_to_sales, "ratio", currency),
            unit="ratio",
            formula="Enterprise Value ├╖ Total Annual Revenue",
            explanation="Compares total enterprise value (debt included, cash deducted) against annual gross revenue.",
            interpretation="A cleaner version of P/S that prevents companies from artificially looking cheap simply by borrowing heavy debt to boost sales."
        )
    )

    # --- 4. Module 2: Growth-Adjusted Valuation ---
    rule_of_40 = None
    if revenue_growth is not None and operating_margin is not None:
        rule_of_40 = (revenue_growth * 100) + (operating_margin * 100)

    price_to_fcf = None
    if market_cap is not None and free_cash_flow and free_cash_flow > 0:
        price_to_fcf = market_cap / free_cash_flow

    growth_val = GrowthValuation(
        peg_ratio=ValuationMetricItem(
            key="peg",
            abbreviation="PEG",
            name="Price/Earnings-to-Growth Ratio",
            value=peg_ratio,
            formatted_value=_format_val(peg_ratio, "ratio", currency),
            unit="ratio",
            formula="P/E Ratio ├╖ Earnings Growth Rate (%)",
            explanation="Standardizes the P/E multiple across differing company growth trajectories.",
            interpretation="PEG < 1.0 implies undervalued relative to earnings expansion; PEG > 2.0 implies premium pricing."
        ),
        rule_of_40=ValuationMetricItem(
            key="rule_of_40",
            abbreviation="Rule of 40",
            name="Rule of 40 Benchmark",
            value=rule_of_40,
            formatted_value=f"{rule_of_40:.1f}%" if rule_of_40 is not None else "Not available",
            unit="percentage",
            formula="Revenue Growth Rate (%) + Operating Margin (%)",
            explanation="Key institutional hurdle metric measuring balance between top-line expansion and profitability.",
            interpretation="A score above 40% represents exceptional performance balancing growth and cash generation."
        ),
        price_to_fcf=ValuationMetricItem(
            key="price_to_fcf",
            abbreviation="P/FCF",
            name="Price to Free Cash Flow",
            value=price_to_fcf,
            formatted_value=_format_val(price_to_fcf, "ratio", currency),
            unit="ratio",
            formula="Market Capitalization ├╖ Free Cash Flow",
            explanation=f"Shows the price paid per {curr_sym}1 of distributable cash generated after essential capital expenditures.",
            interpretation="Often considered more reliable than P/E because reported net profits can be distorted by non-cash accounting adjustments."
        ),
        fcf_growth=ValuationMetricItem(
            key="fcf_growth",
            abbreviation="FCF Growth",
            name="Free Cash Flow YoY Growth",
            value=fcf_growth,
            formatted_value=_format_val(fcf_growth, "percentage", currency),
            unit="percentage",
            formula="(Current FCF - Previous FCF) ├╖ Previous FCF",
            explanation="Measures annual expansion in the company's real cash generation capacity.",
            interpretation="Sustained positive cash flow growth provides fuel for dividends, share buybacks, and debt reduction."
        ),
        profit_growth=ValuationMetricItem(
            key="profit_growth",
            abbreviation="Profit Growth",
            name="Net Profit YoY Growth",
            value=profit_growth,
            formatted_value=_format_val(profit_growth, "percentage", currency),
            unit="percentage",
            formula="(Current Net Profit - Previous Net Profit) ├╖ Previous Net Profit",
            explanation="Year-over-year rate of bottom-line earnings change.",
            interpretation="Rapid profit growth supports higher baseline valuation multiples."
        )
    )

    # --- 5. Module 3: Historical Valuation ---
    historical_points = []
    pe_history = []
    for d in sorted(dates_desc):
        h_rev = _get_val(inc_stmt, d, ['Total Revenue', 'Operating Revenue'])
        h_np = _get_val(inc_stmt, d, ['Net Income', 'Net Income Common Stockholders'])
        h_op_inc = _get_val(inc_stmt, d, ['Operating Income', 'EBIT'])
        
        h_op_margin = (h_op_inc / h_rev) if (h_op_inc is not None and h_rev and h_rev > 0) else None
        h_net_margin = (h_np / h_rev) if (h_np is not None and h_rev and h_rev > 0) else None
        h_est_pe = (market_cap / h_np) if (market_cap and h_np and h_np > 0) else None

        if h_est_pe and h_est_pe > 0:
            pe_history.append(h_est_pe)

        historical_points.append(HistoricalValuationPoint(
            date=d,
            revenue=h_rev,
            net_profit=h_np,
            operating_margin=h_op_margin,
            net_margin=h_net_margin,
            estimated_pe=h_est_pe
        ))

    avg_pe = (sum(pe_history) / len(pe_history)) if pe_history else None
    current_vs_avg_pe = None
    if pe_ratio and avg_pe and avg_pe > 0:
        current_vs_avg_pe = ((pe_ratio - avg_pe) / avg_pe) * 100

    hist_val = HistoricalValuation(
        history=historical_points,
        avg_pe=avg_pe,
        current_vs_avg_pe_pct=current_vs_avg_pe,
        description=f"Evaluates how current multiples compare to the company's historical averages across {len(historical_points)} reported periods."
    )

    # --- 6. Module 4: Relative / Peer Valuation ---
    sector = profile.sector or "General Market"
    industry = profile.industry or "General Industry"
    benchmark = SECTOR_BENCHMARKS.get(sector, DEFAULT_SECTOR_BENCHMARK)
    benchmark_pe = benchmark["pe"]
    benchmark_pb = benchmark["pb"]
    benchmark_ev_ebitda = benchmark["ev_ebitda"]

    pe_discount_premium = None
    status_badge = "In-Line with Sector"
    if pe_ratio and benchmark_pe:
        pe_discount_premium = ((pe_ratio - benchmark_pe) / benchmark_pe) * 100
        if pe_discount_premium < -15:
            status_badge = f"Trading at {abs(pe_discount_premium):.1f}% Discount to Sector"
        elif pe_discount_premium > 15:
            status_badge = f"Trading at {pe_discount_premium:.1f}% Premium to Sector"
        else:
            status_badge = "Fairly Valued Relative to Sector Peers"

    relative_val = RelativeValuation(
        sector=sector,
        industry=industry,
        stock_pe=pe_ratio,
        benchmark_pe=benchmark_pe,
        pe_discount_premium_pct=pe_discount_premium,
        stock_pb=pb_ratio,
        benchmark_pb=benchmark_pb,
        stock_ev_ebitda=ev_to_ebitda,
        benchmark_ev_ebitda=benchmark_ev_ebitda,
        status_badge=status_badge,
        description=f"Comparing multiples against typical {sector} industry hurdles."
    )

    # --- 7. Module 5: Discounted Cash Flow (DCF) Valuation ---
    # Safe handling: Disclose assumptions, mark unavailable if FCF <= 0 or missing
    dcf_available = False
    dcf_reason = None
    dcf_assumptions = DCFAssumptions()
    projected_fcf_list = []
    terminal_val = None
    pv_tv = None
    dcf_ev = None
    dcf_equity = None
    intrinsic_val = None
    margin_of_safety = None

    if free_cash_flow is None:
        dcf_reason = "Free Cash Flow statement data is missing. DCF cannot be calculated without verified baseline cash flows."
    elif free_cash_flow <= 0:
        dcf_reason = "Free Cash Flow is negative or zero. Intrinsic DCF projections require positive sustainable cash flow to avoid speculative extrapolation."
    elif not profile.shares_outstanding or profile.shares_outstanding <= 0:
        dcf_reason = "Shares outstanding count is unavailable to compute intrinsic value per share."
    else:
        dcf_available = True
        # Conservative assumptions
        fcf_growth_assumption = 10.0
        if profit_growth and profit_growth > 0:
            fcf_growth_assumption = min(max(profit_growth * 100, 5.0), 15.0)

        discount_rate = 10.5  # 10.5% standard cost of capital
        term_growth = 3.0     # 3% terminal rate
        net_debt_val = (total_debt or 0) - (cash or 0)
        shares_out = profile.shares_outstanding

        dcf_assumptions = DCFAssumptions(
            base_fcf=free_cash_flow,
            growth_rate_pct=round(fcf_growth_assumption, 1),
            discount_rate_pct=discount_rate,
            terminal_growth_rate_pct=term_growth,
            forecast_years=5,
            net_debt=net_debt_val,
            shares_outstanding=shares_out
        )

        g = fcf_growth_assumption / 100.0
        r = discount_rate / 100.0
        gt = term_growth / 100.0

        curr_fcf_proj = free_cash_flow
        pv_sum = 0.0

        for year in range(1, 6):
            curr_fcf_proj = curr_fcf_proj * (1 + g)
            pv_cf = curr_fcf_proj / ((1 + r) ** year)
            pv_sum += pv_cf
            projected_fcf_list.append({
                "year": f"Year {year}",
                "projected_fcf": curr_fcf_proj,
                "present_value": pv_cf
            })

        if r > gt:
            terminal_val = (curr_fcf_proj * (1 + gt)) / (r - gt)
            pv_tv = terminal_val / ((1 + r) ** 5)
            dcf_ev = pv_sum + pv_tv
            dcf_equity = dcf_ev - net_debt_val
            if dcf_equity > 0 and shares_out > 0:
                intrinsic_val = dcf_equity / shares_out
                if profile.current_price and profile.current_price > 0:
                    margin_of_safety = ((intrinsic_val - profile.current_price) / profile.current_price) * 100

    dcf_val = DCFValuation(
        is_available=dcf_available,
        reason=dcf_reason,
        assumptions=dcf_assumptions,
        projected_fcf=projected_fcf_list,
        terminal_value=terminal_val,
        present_value_terminal=pv_tv,
        enterprise_value=dcf_ev,
        equity_value=dcf_equity,
        intrinsic_value_per_share=intrinsic_val,
        current_price=profile.current_price,
        margin_of_safety_pct=margin_of_safety,
        description="Transparent 5-year discounted cash flow model. All discount rate and growth assumptions are fully disclosed."
    )

    # --- 8. Module 6: Valuation Quality and Risk ---
    interest_coverage = None
    if ebit is not None and interest_expense:
        abs_interest = abs(interest_expense)
        if abs_interest > 0:
            interest_coverage = ebit / abs_interest

    cash_conversion = None
    if free_cash_flow is not None and net_profit and net_profit > 0:
        cash_conversion = free_cash_flow / net_profit

    risk_badge = "Moderate Balance Sheet Risk"
    if debt_to_equity is not None and debt_to_equity < 0.5:
        if interest_coverage is None or interest_coverage > 5.0:
            risk_badge = "Low Financial Leverage Risk"
    elif debt_to_equity is not None and debt_to_equity > 1.5:
        risk_badge = "Elevated Financial Leverage"

    quality_risk = ValuationQualityRisk(
        interest_coverage=ValuationMetricItem(
            key="interest_coverage",
            abbreviation="Interest Coverage",
            name="Interest Coverage Ratio",
            value=interest_coverage,
            formatted_value=_format_val(interest_coverage, "ratio", currency),
            unit="ratio",
            formula="Operating Profit (EBIT) ├╖ Annual Interest Expense",
            explanation="Measures how many times the company's operating earnings can pay its ongoing debt interest expenses.",
            interpretation="A ratio above 3.0x is generally considered safe. Ratios under 1.5x indicate potential distress if profits decline."
        ),
        debt_to_equity=ValuationMetricItem(
            key="debt_to_equity",
            abbreviation="D/E",
            name="Debt-to-Equity Ratio",
            value=debt_to_equity,
            formatted_value=_format_val(debt_to_equity, "ratio", currency),
            unit="ratio",
            formula="Total Debt ├╖ Stockholders' Equity",
            explanation="Compares total borrowed money against the equity cushion contributed by shareholders.",
            interpretation="D/E below 0.5 indicates conservative financial leverage; D/E above 1.5 signals heavy reliance on borrowed debt."
        ),
        cash_conversion=ValuationMetricItem(
            key="cash_conversion",
            abbreviation="FCF / Net Income",
            name="Earnings Quality (Cash Conversion)",
            value=cash_conversion,
            formatted_value=_format_val(cash_conversion, "ratio", currency),
            unit="ratio",
            formula="Free Cash Flow ├╖ Net Income",
            explanation="Measures how much of reported accounting net income is backed by hard cash flow after capital expenditures.",
            interpretation="Ratios near or above 1.0 indicate high-quality earnings. Ratios consistently below 0.5 indicate accrual earnings not translating to cash."
        ),
        beta=ValuationMetricItem(
            key="beta",
            abbreviation="Beta",
            name="Market Sensitivity (Beta)",
            value=profile.beta,
            formatted_value=_format_val(profile.beta, "ratio", currency),
            unit="ratio",
            formula="Covariance(Stock, Market) ├╖ Variance(Market)",
            explanation="Measures systemic volatility of the stock relative to the broader benchmark market index.",
            interpretation="Beta = 1.0 moves in tandem with the market; Beta < 1.0 indicates lower volatility; Beta > 1.2 indicates higher volatility."
        ),
        overall_risk_badge=risk_badge,
        description="Assesses capital structure resilience, cash generation quality, and systemic market risk."
    )

    valuation_modules = ValuationModules(
        earnings_valuation=earnings_val,
        growth_valuation=growth_val,
        historical_valuation=hist_val,
        relative_valuation=relative_val,
        dcf_valuation=dcf_val,
        quality_risk=quality_risk
    )

    # --- 9. Historical Data (Existing Charting Compatibility) ---
    historical_data = []
    for d in sorted(dates_desc):
        h_rev = _get_val(inc_stmt, d, ['Total Revenue', 'Operating Revenue'])
        h_np = _get_val(inc_stmt, d, ['Net Income', 'Net Income Common Stockholders'])
        h_op_inc = _get_val(inc_stmt, d, ['Operating Income', 'EBIT'])
        
        h_op_margin = (h_op_inc / h_rev) if (h_op_inc is not None and h_rev and h_rev > 0) else None
            
        historical_data.append(HistoricalMetric(
            date=d,
            revenue=h_rev,
            net_profit=h_np,
            operating_margin=h_op_margin
        ))

    calculated_metrics = CalculatedMetrics(
        revenue=revenue,
        revenue_growth=revenue_growth,
        net_profit=net_profit,
        profit_growth=profit_growth,
        roe=roe,
        roce=roce,
        debt_to_equity=debt_to_equity,
        operating_margin=operating_margin,
        free_cash_flow=free_cash_flow,
        pe_ratio=pe_ratio,
        forward_pe=forward_pe,
        peg_ratio=peg_ratio,
        ps_ratio=ps_ratio,
        pb_ratio=pb_ratio,
        ev_to_ebitda=ev_to_ebitda,
        ev_to_ebit=ev_to_ebit,
        ev_to_sales=ev_to_sales
    )

    logger.info(f"Successfully calculated metrics and valuation for {data.profile.ticker}")
    return FinancialMetricsResult(
        metrics=calculated_metrics,
        historical_data=historical_data,
        valuation=valuation_modules
    )
