# 기업 정보 관련 API
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.company import CompanyInfo
from app.services.crawler import get_company_info_from_yahoo
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol

router = APIRouter()

@router.get("/companies/{stock_symbol}", response_model=CompanyInfo)
def get_company_info(stock_symbol: str, date: Optional[str] = Query(None, description="조회 기준 날짜 (YYYY-MM-DD)"), granularity: Optional[str] = Query("year", description="조회 단위: day/month/year")):
    data = get_company_info_from_yahoo(stock_symbol, date=date, granularity=granularity)
    if not data.get("company_name") or "정보 없음" in data["company_name"]:
        raise HTTPException(status_code=404, detail="해당 기업 정보를 찾을 수 없습니다.")
    return data

@router.get("/sentiment/weekly")
def get_weekly_sentiment(
    stock_symbol: str = Query(..., description="주식 심볼"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)")
):
    """
    입력받은 기업명(심볼)과 기간에 대해 주차별 감성점수 반환
    """
    result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    # 리스트로 변환하여 score가 float임을 보장
    return [{"week": week, "score": float(score)} for week, score in result.items()]
