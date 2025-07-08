# 기업 정보 관련 API
from fastapi import APIRouter, HTTPException, Query
from typing import Optional


from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
from app.services.crawler import (
    get_company_profile_from_alphavantage,
    get_financial_statements_from_sec,
    get_weekly_stock_indicators_from_stooq
)
from app.core.config import settings

router = APIRouter()

# 기업 기본 정보만 반환하는 API
@router.get("/companies/{stock_symbol}/info")
def get_company_basic_info(stock_symbol: str):
    profile = get_company_profile_from_alphavantage(stock_symbol, settings.ALPHAVANTAGE_API_KEY)
    return {
        "company_name": profile.get("company_name") or stock_symbol,
        "stock_symbol": stock_symbol,
        "industry": profile.get("industry"),
        "sector": profile.get("sector"),
        "business_summary": profile.get("description"),
        "address": profile.get("address")
    }

# 기업 정보 조회 API
@router.get("/companies/{stock_symbol}")
def get_company_info(
    stock_symbol: str,
    start_date: Optional[str] = Query(None, description="조회 시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료일 (YYYY-MM-DD)"),
    granularity: Optional[str] = Query("year", description="조회 단위: day/month/year")
):
    # Alpha Vantage 기업 개요
    profile = get_company_profile_from_alphavantage(stock_symbol, settings.ALPHAVANTAGE_API_KEY)
    # SEC 재무제표
    financials = get_financial_statements_from_sec(stock_symbol, start_date=start_date, end_date=end_date)
    # Stooq 주가/기술지표 (이동평균 제외)
    import datetime
    if end_date:
        # start_date가 없으면 end_date 기준 7일 전
        start = start_date if start_date else (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
        end = end_date
    else:
        end = datetime.datetime.today().strftime("%Y-%m-%d")
        start = (datetime.datetime.today() - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
    indicators = get_weekly_stock_indicators_from_stooq(stock_symbol, start, end)
    return {
        "company_info": {
            "company_name": profile.get("company_name") or stock_symbol,
            "stock_symbol": stock_symbol,
            "industry": profile.get("industry"),
            "sector": profile.get("sector"),
            "business_summary": profile.get("description"),
            "address": profile.get("address")
        },
        "income_statements": financials,
        "weekly_indicators": indicators
    }

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None  # 변환 불가 시 None 반환

