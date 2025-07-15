from fastapi import APIRouter, HTTPException
from app.services.crawler import get_valuation_metrics_from_fmp
from typing import Optional

router = APIRouter()

@router.get("/valuation")
async def get_valuation_metrics(symbol: str, end_date: Optional[str] = None):
    """
    벨류에이션 지표 조회 API
    - EPS, P/E, P/B, ROE(%)
    - 당해연도, 전연도 데이터
    """
    try:
        result = get_valuation_metrics_from_fmp(symbol, end_date)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벨류에이션 지표 조회 실패: {str(e)}")
