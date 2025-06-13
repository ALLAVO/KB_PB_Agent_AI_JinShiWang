from fastapi import APIRouter, Query
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
from app.services.summarize import summarize_article
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

@router.get("/sentiment/weekly_with_summary")
def weekly_sentiment_with_summary(
        stock_symbol: str = Query(...),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None)):
    """
    주식 심볼별 주차별 감성점수와 기사 요약 반환 API
    """
    sentiment_result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    summary_result = summarize_article(stock_symbol, start_date, end_date)
    return {
        "sentiment": sentiment_result,
        "summaries": summary_result
    }
