from fastapi import APIRouter, Query
from typing import Dict, Any
from app.services.summarize import get_weekly_top3_summaries

router = APIRouter()

@router.get("/summarize/weekly")
def get_weekly_summarize(
    stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
    start_date: str = Query(..., description="시작일, 예: '2023-12-11'"),
    end_date: str = Query(..., description="종료일, 예: '2023-12-14'")
) -> Dict[str, Any]:
    """
    주차별 top3 기사 요약 결과 반환
    """
    result = get_weekly_top3_summaries(stock_symbol, start_date, end_date)
    return result

