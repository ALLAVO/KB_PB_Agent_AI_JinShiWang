from fastapi import APIRouter, HTTPException, Query
from app.services.return_analysis import ReturnAnalysisService

router = APIRouter()

@router.get("/return-analysis/comparison")
async def get_return_comparison(
    symbol: str = Query(..., description="종목 코드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """
    개별 주식과 나스닥의 수익률 비교 데이터를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    """
    try:
        result = ReturnAnalysisService.get_return_comparison(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/return-analysis/summary")
async def get_analysis_summary(
    symbol: str = Query(..., description="종목 코드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """
    수익률 분석 요약 정보를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    """
    try:
        result = ReturnAnalysisService.get_analysis_summary(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/return-analysis/combined-chart")
async def get_combined_chart_data(
    symbol: str = Query(..., description="종목 코드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """
    차트용 결합된 수익률 데이터를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    """
    try:
        result = ReturnAnalysisService.get_combined_chart_data(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
