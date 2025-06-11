from fastapi import APIRouter, Query
from app.services import sentiment
from typing import Optional

router = APIRouter(
    prefix="/api/sentiment",
    tags=["sentiment"]
)

@router.get("/weekly")
def get_weekly_sentiment(
    stock_symbol: str = Query(..., description="주식 심볼"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)")
):
    # 실제 감성점수 계산 로직은 sentiment 서비스에서 구현되어야 함
    articles = sentiment.get_articles_by_stock_symbol(stock_symbol, start_date, end_date)
    # 예시: 기사 수 반환 (실제 감성점수 로직으로 대체 필요)
    return {"stock_symbol": stock_symbol, "start_date": start_date, "end_date": end_date, "article_count": len(articles) if articles else 0}

