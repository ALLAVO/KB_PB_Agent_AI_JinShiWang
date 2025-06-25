from fastapi import APIRouter, Query
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
from app.services.summarize import summarize_article
from typing import Optional
from app.schemas.sentiment import WeeklySentimentResponse, WeeklySentimentWithSummaryResponse

router = APIRouter()

# 주식 심볼별 주차별 감성점수 반환 API
@router.get("/sentiment/weekly", response_model=WeeklySentimentResponse)
def weekly_sentiment_scores(
        stock_symbol: str = Query(...),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None)):
    """
    주식 심볼별 주차별 감성점수 반환 API
    """
    result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    if not result or not isinstance(result, dict):
        return {"weekly_scores": {}, "weekly_top3_articles": {}}
    # weekly_scores와 weekly_top3_articles 키가 항상 포함되도록 보장
    return {
        "weekly_scores": result.get("weekly_scores", {}),
        "weekly_top3_articles": result.get("weekly_top3_articles", {})
    }

@router.get("/sentiment/weekly_with_summary", response_model=WeeklySentimentWithSummaryResponse)
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
        "sentiment": sentiment_result if sentiment_result else {},
        "summaries": summary_result if summary_result else {}
    }
