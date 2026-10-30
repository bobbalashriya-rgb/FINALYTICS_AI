import logging
import pandas as pd
import yfinance as yf
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Configure logger for the financial data layer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Normalized Internal Data Models
# ---------------------------------------------------------

class CompanyProfile(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[int] = None
    currency: Optional[str] = "USD"
    shares_outstanding: Optional[int] = None
    enterprise_value: Optional[float] = None
    forward_pe: Optional[float] = None
    trailing_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_book: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    book_value: Optional[float] = None
    beta: Optional[float] = None

class HistoricalPrice(BaseModel):
    date: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]

class FinancialStatements(BaseModel):
    income_statement: Dict[str, Any]
    balance_sheet: Dict[str, Any]
    cash_flow: Dict[str, Any]

class NormalizedCompanyData(BaseModel):
    profile: CompanyProfile
    financials: FinancialStatements
    historical_prices: List[HistoricalPrice]

class FinancialDataError(Exception):
    """Custom exception raised for errors during financial data retrieval."""
    pass

# ---------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------

def _clean_dataframe_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Safely converts a pandas DataFrame from yfinance to a built-in dictionary.
    Replaces NaNs with None to avoid hallucinated/estimated values and 
    formats Timestamp columns to ISO date strings.
    """
    if df is None or df.empty:
        return {}
    
    # Cast to object to safely insert None in place of NaN
    cleaned_df = df.astype(object).where(pd.notnull(df), None)
    
    # Convert column headers (usually dates) to strings
    cleaned_df.columns = [
        col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col) 
        for col in cleaned_df.columns
    ]
    
    return cleaned_df.to_dict()

def fetch_company_data(ticker: str) -> NormalizedCompanyData:
    """
    Fetches comprehensive financial data for a given ticker from yfinance.
    Normalizes the response into a structured, internal data model.
    """
    logger.info(f"Initiating data retrieval for ticker: {ticker}")
    
    try:
        stock = yf.Ticker(ticker)
        
        # 1. Fetch Company Profile & Info
        info = stock.info
        
        # Check for invalid/unavailable ticker heuristic
        # yfinance often returns dicts with only 'trailingPegRatio' or an empty dict for bad tickers
        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info and 'shortName' not in info):
            error_msg = f"No valid company data found for ticker {ticker}. It may be invalid or delisted."
            logger.warning(error_msg)
            raise FinancialDataError(error_msg)

        def _safe_float(val):
            try:
                return float(val) if val is not None else None
            except (ValueError, TypeError):
                return None

        def _safe_int(val):
            try:
                return int(val) if val is not None else None
            except (ValueError, TypeError):
                return None

        currency_val = info.get('currency') or ('INR' if ticker.upper().endswith(('.NS', '.BO')) else 'USD')

        profile = CompanyProfile(
            ticker=ticker,
            name=info.get('shortName') or info.get('longName'),
            sector=info.get('sector'),
            industry=info.get('industry'),
            current_price=_safe_float(info.get('currentPrice') or info.get('regularMarketPrice')),
            market_cap=_safe_int(info.get('marketCap')),
            currency=currency_val,
            shares_outstanding=_safe_int(info.get('sharesOutstanding')),
            enterprise_value=_safe_float(info.get('enterpriseValue')),
            forward_pe=_safe_float(info.get('forwardPE')),
            trailing_pe=_safe_float(info.get('trailingPE')),
            peg_ratio=_safe_float(info.get('pegRatio')),
            price_to_sales=_safe_float(info.get('priceToSalesTrailing12Months')),
            price_to_book=_safe_float(info.get('priceToBook')),
            ev_to_ebitda=_safe_float(info.get('enterpriseToEbitda')),
            ev_to_revenue=_safe_float(info.get('enterpriseToRevenue')),
            book_value=_safe_float(info.get('bookValue')),
            beta=_safe_float(info.get('beta')),
        )
        logger.info(f"Successfully retrieved profile for {profile.name or ticker} ({ticker})")
        
        # 2. Fetch Financial Statements
        logger.info(f"Fetching financial statements for {ticker}...")
        inc_stmt = stock.financials
        bal_sheet = stock.balance_sheet
        cash_flw = stock.cashflow
        
        financials = FinancialStatements(
            income_statement=_clean_dataframe_to_dict(inc_stmt),
            balance_sheet=_clean_dataframe_to_dict(bal_sheet),
            cash_flow=_clean_dataframe_to_dict(cash_flw)
        )
        
        # 3. Fetch Historical Price Data
        logger.info(f"Fetching historical price data for {ticker} (1 year)...")
        history_df = stock.history(period="1y")
        
        historical_prices = []
        if not history_df.empty:
            hist_reset = history_df.reset_index()
            for _, row in hist_reset.iterrows():
                # Safely extract date
                date_val = row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
                
                historical_prices.append(HistoricalPrice(
                    date=date_val,
                    open=row['Open'] if pd.notna(row['Open']) else None,
                    high=row['High'] if pd.notna(row['High']) else None,
                    low=row['Low'] if pd.notna(row['Low']) else None,
                    close=row['Close'] if pd.notna(row['Close']) else None,
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else None
                ))
        else:
            logger.warning(f"No historical price data returned for {ticker}.")
            
        logger.info(f"Successfully normalized all data for {ticker}.")
        
        return NormalizedCompanyData(
            profile=profile,
            financials=financials,
            historical_prices=historical_prices
        )
        
    except FinancialDataError:
        # Re-raise the custom error without wrapping it
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving financial data for {ticker}: {str(e)}", exc_info=True)
        raise FinancialDataError(f"Failed to fetch financial data for {ticker}. The service may be temporarily unavailable.") from e

