from fastapi import APIRouter, Query
from typing import Optional
from app.services.crawler import get_us_stock_indices_range, get_us_treasury_yields_range, get_kr_fx_rates_range
from app.core.config import settings

router = APIRouter()

@router.get("/market/overview")
def get_market_overview(
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """
    미국 증시 지수, 미국 국채 금리, 한국 환율(USD/KRW, EUR/KRW) 시황정보를 기간 평균으로 반환
    """
    indices = get_us_stock_indices_range(start_date, end_date)
    yields = get_us_treasury_yields_range(settings.FRED_API_KEY, start_date, end_date)
    fx = get_kr_fx_rates_range(None, start_date, end_date)
    return {
        "us_stock_indices": indices,
        "us_treasury_yields": yields,
        "kr_fx_rates": fx
    }
