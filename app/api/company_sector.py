"""
기업 섹터 정보 API
"""
from fastapi import APIRouter, HTTPException
from app.services.company_sector_service import get_company_sector_by_ticker
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/companies/{ticker}/sector")
async def get_company_sector(ticker: str):
    """
    기업의 티커로 섹터 정보를 조회하는 API
    
    Args:
        ticker (str): 기업 티커 심볼
        
    Returns:
        dict: 섹터 정보
    """
    try:
        # 티커를 대문자로 변환
        ticker = ticker.upper()
        
        # 섹터 정보 조회
        result = get_company_sector_by_ticker(ticker)
        
        if result.get("sector") is None and "message" in result:
            raise HTTPException(status_code=404, detail=result["message"])
            
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_sector API for ticker {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
