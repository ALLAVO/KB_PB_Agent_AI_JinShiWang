from fastapi import APIRouter, Query
from typing import Optional
from app.services.crawler import get_us_indices_6months_chart, get_us_treasury_yields_6months, get_kr_fx_rates_6months, get_commodity_prices_6months
from app.core.config import settings

router = APIRouter()

# 미국/한국 주요 지수, 금리, 환율, 원자재 가격 관련 API
@router.get("/market/indices-6months-chart")
def get_us_indices_6months_chart_api(
    end_date: str = Query(..., description="그래프 마지막 날짜 (YYYY-MM-DD)")
):
    """
    미국 DOW, S&P500, NASDAQ 6개월치 일별 종가 그래프 데이터를 반환합니다.
    """
    return get_us_indices_6months_chart(end_date)

# 원자재 가격 6개월치 일별 데이터 API
@router.get("/market/treasury-yields-6months-chart")
def get_us_treasury_yields_6months_api(
    end_date: str = Query(..., description="그래프 마지막 날짜 (YYYY-MM-DD)")
):
    """
    미국 국채 2년/10년물 6개월치 일별 금리 데이터를 반환합니다.
    """
    return get_us_treasury_yields_6months(settings.FRED_API_KEY, end_date)

# 원자재 가격 6개월치 일별 데이터 API
@router.get("/market/fx-6months-chart")
def get_kr_fx_rates_6months_api(
    end_date: str = Query(..., description="그래프 마지막 날짜 (YYYY-MM-DD)")
):
    """
    USD/KRW, EUR/USD 6개월치 일별 환율 데이터를 반환합니다.
    """
    return get_kr_fx_rates_6months(end_date)
