from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
from app.services.crawler import get_financial_metrics_from_sec

router = APIRouter()

@router.get("/financial-metrics/{symbol}")
async def get_financial_metrics(symbol: str, end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")) -> Dict:
    """
    기업의 재무지표를 반환합니다.
    - 매출액, 영업이익, 영업이익률, 순이익
    - 당해연도, 전연도 데이터
    - end_date: 해당 날짜를 기준으로 연도 계산 (선택사항)
    """
    try:
        result = get_financial_metrics_from_sec(symbol.upper(), end_date)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching financial metrics: {str(e)}")
