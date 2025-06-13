from fastapi import APIRouter, Query
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
from typing import Optional

router = APIRouter()

@router.get("/sentiment/weekly")
def weekly_sentiment_scores(
    stock_symbol: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)):
    """
    주식 심볼별 주차별 감성점수 반환 API
    """
    result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    if isinstance(result, int):
        return {"score": result}
    return result
