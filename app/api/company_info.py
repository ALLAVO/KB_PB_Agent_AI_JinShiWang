# 기업 정보 관련 API
from fastapi import APIRouter, Query
from typing import Optional

from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
from app.services.crawler import (
    get_company_profile_from_alphavantage,
    get_financial_statements_from_sec,
    get_weekly_stock_indicators_from_stooq,
    get_moving_averages_from_stooq
)
from app.core.config import settings

router = APIRouter()

# 기업 재무 및 밸류에이션 데이터 API
@router.get("/companies/{stock_symbol}/financial-analysis")
def get_company_financial_analysis(
    stock_symbol: str,
    start_date: Optional[str] = Query(None, description="조회 시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료일 (YYYY-MM-DD)")
):
    import datetime
    
    # Alpha Vantage 기업 개요 (밸류에이션 지표 포함)
    profile = get_company_profile_from_alphavantage(stock_symbol, settings.ALPHAVANTAGE_API_KEY)
    
    # SEC 재무제표
    financials = get_financial_statements_from_sec(stock_symbol, start_date=start_date, end_date=end_date)
    
    # 주가 정보
    if end_date:
        start = start_date if start_date else (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
        end = end_date
    else:
        end = datetime.datetime.today().strftime("%Y-%m-%d")
        start = (datetime.datetime.today() - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
    
    indicators = get_weekly_stock_indicators_from_stooq(stock_symbol, start, end)
    ma = get_moving_averages_from_stooq(stock_symbol, end)
    
    # 재무 지표 계산
    def safe_get(data, key, default=None):
        if isinstance(data, dict) and key in data and data[key].get('value') is not None:
            return data[key]['value']
        return default
    
    def safe_divide(a, b):
        try:
            if a is not None and b is not None and b != 0:
                return round(a / b, 2)
        except:
            pass
        return None
    
    # 기본 재무 데이터 추출
    revenues = safe_get(financials, 'Revenues') or safe_get(financials, 'SalesRevenueNet')
    net_income = safe_get(financials, 'NetIncomeLoss')
    total_assets = safe_get(financials, 'Assets')
    total_liabilities = safe_get(financials, 'Liabilities')
    stockholders_equity = safe_get(financials, 'StockholdersEquity')
    current_assets = safe_get(financials, 'AssetsCurrent')
    current_liabilities = safe_get(financials, 'LiabilitiesCurrent')
    operating_income = safe_get(financials, 'OperatingIncomeLoss')
    cash_flow_ops = safe_get(financials, 'NetCashProvidedByUsedInOperatingActivities')
    shares_outstanding = safe_get(financials, 'CommonStockSharesOutstanding')
    
    # Alpha Vantage에서 추가 정보
    market_cap = profile.get('MarketCapitalization')
    pe_ratio = profile.get('PERatio')
    pb_ratio = profile.get('PriceToBookRatio')
    dividend_yield = profile.get('DividendYield')
    beta = profile.get('Beta')
    eps = profile.get('EPS')
    book_value = profile.get('BookValue')
    price_to_sales = profile.get('PriceToSalesRatioTTM')
    
    # 비율 계산
    current_ratio = safe_divide(current_assets, current_liabilities)
    debt_to_equity = safe_divide(total_liabilities, stockholders_equity)
    roe = safe_divide(net_income, stockholders_equity) * 100 if net_income and stockholders_equity else None
    roa = safe_divide(net_income, total_assets) * 100 if net_income and total_assets else None
    profit_margin = safe_divide(net_income, revenues) * 100 if net_income and revenues else None
    
    # 재무 건전성 데이터
    financial_health = {
        "유동비율": {"value": current_ratio, "unit": "배", "description": "유동자산 / 유동부채"},
        "부채비율": {"value": debt_to_equity, "unit": "배", "description": "총부채 / 자기자본"},
        "자기자본비율": {"value": safe_divide(stockholders_equity, total_assets) * 100 if stockholders_equity and total_assets else None, "unit": "%", "description": "자기자본 / 총자산"},
    }
    
    # 수익성 지표
    profitability = {
        "매출액": {"value": revenues, "unit": "USD", "description": "총 매출액"},
        "순이익": {"value": net_income, "unit": "USD", "description": "당기순이익"},
        "영업이익": {"value": operating_income, "unit": "USD", "description": "영업활동으로 인한 이익"},
        "순이익률": {"value": profit_margin, "unit": "%", "description": "순이익 / 매출액"},
        "ROE": {"value": roe, "unit": "%", "description": "자기자본이익률"},
        "ROA": {"value": roa, "unit": "%", "description": "총자산이익률"},
    }
    
    # 밸류에이션 지표
    valuation = {
        "시가총액": {"value": safe_float(market_cap), "unit": "USD", "description": "발행주식수 × 주가"},
        "PER": {"value": safe_float(pe_ratio), "unit": "배", "description": "주가수익비율"},
        "PBR": {"value": safe_float(pb_ratio), "unit": "배", "description": "주가순자산비율"},
        "PSR": {"value": safe_float(price_to_sales), "unit": "배", "description": "주가매출비율"},
        "EPS": {"value": safe_float(eps), "unit": "USD", "description": "주당순이익"},
        "BPS": {"value": safe_float(book_value), "unit": "USD", "description": "주당순자산"},
        "배당수익률": {"value": safe_float(dividend_yield), "unit": "%", "description": "연간배당금 / 주가"},
        "베타": {"value": safe_float(beta), "unit": "", "description": "시장 대비 변동성"},
    }
    
    # 주가 정보
    stock_info = {
        "현재주가": {"value": indicators.get('close_avg'), "unit": "USD", "description": "최근 평균 종가"},
        "주간변동률": {"value": indicators.get('price_change_pct'), "unit": "%", "description": "주간 주가 변동률"},
        "변동성": {"value": indicators.get('volatility'), "unit": "USD", "description": "주가 변동성"},
        "거래량": {"value": indicators.get('volume_avg'), "unit": "주", "description": "평균 거래량"},
        "이동평균(5일)": {"value": ma.get('ma5'), "unit": "USD", "description": "5일 이동평균"},
        "이동평균(20일)": {"value": ma.get('ma20'), "unit": "USD", "description": "20일 이동평균"},
    }
    
    return {
        "company_name": profile.get("company_name") or stock_symbol,
        "stock_symbol": stock_symbol,
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "business_summary": profile.get("description"),
        "financial_health": financial_health,
        "profitability": profitability,
        "valuation": valuation,
        "stock_info": stock_info,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

