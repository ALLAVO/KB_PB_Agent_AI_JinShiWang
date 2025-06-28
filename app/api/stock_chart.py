from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.services.stock_chart import StockChartService

router = APIRouter()

@router.get("/stock-chart/summary")
async def get_stock_chart_summary(
    symbol: str = Query(..., description="종목 코드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """
    주가 차트 요약 정보를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    """
    try:
        result = StockChartService.get_chart_summary(
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

@router.get("/stock-chart/combined-chart")
async def get_combined_chart_get(
    symbol: str = Query(..., description="종목 코드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)"),
    chart_types: str = Query("price", description="차트 타입들 (콤마로 구분: price,moving_average,volume,relative_nasdaq)"),
    ma_periods: str = Query("5,20,60", description="이동평균 기간들 (콤마로 구분)")
):
    """
    여러 차트 타입을 조합한 주가 차트 데이터를 반환합니다. (GET 방식)
    
    - **chart_types**: price (주가), moving_average (이동평균), volume (거래량), relative_nasdaq (나스닥 대비 상대지수)
    """
    try:
        # 문자열을 리스트로 변환
        chart_types_list = [ct.strip() for ct in chart_types.split(",")]
        ma_periods_list = [int(mp.strip()) for mp in ma_periods.split(",")]
        
        result = StockChartService.get_combined_chart(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date,
            chart_types=chart_types_list,
            ma_periods=ma_periods_list
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")