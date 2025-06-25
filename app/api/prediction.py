from fastapi import APIRouter, Query
from typing import Optional
from app.services.prediction import get_summary_from_openai_by_params

router = APIRouter()

@router.get("/prediction/weekly")
def weekly_keyword_extraction(
        stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
        start_date: Optional[str] = Query(None, description="시작일, 예: '2023-12-11'"),
        end_date: Optional[str] = Query(None, description="종료일, 예: '2023-12-14'")
):
    """
    주식 심볼별 주차별 기사별 키워드 추출 API
    """
    result = get_summary_from_openai_by_params(stock_symbol, start_date, end_date)
    return result