from fastapi import APIRouter, Query
from typing import Optional
from app.services.keyword_extractor import keyword_extract_from_articles

router = APIRouter()

@router.get(
    "/keyword/weekly",
    summary="선택한 기업의 해당 주차에 대한 Top-3 기사의 키워드 추출",
    description="주식 심볼, 시작일, 종료일을 입력받아 해당 기간 내 주차별 article 중 top-3 ariticle의 주요 키워드를 추출합니다.",
    tags=["article analyze"]
)
def weekly_keyword_extraction(
    stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
    start_date: Optional[str] = Query(None, description="시작일, 예: '2023-12-11'"),
    end_date: Optional[str] = Query(None, description="종료일, 예: '2023-12-14'")
):
    """
    주식 심볼별 주차별 기사별 키워드 추출 API
    """
    result = keyword_extract_from_articles(stock_symbol, start_date, end_date)
    return result
