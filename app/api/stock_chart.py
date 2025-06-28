from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.stock_chart import StockChartService

router = APIRouter()

class StockChartRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    chart_type: Optional[str] = "price"
    ma_periods: Optional[List[int]] = [5, 20, 60]

class PeriodChartRequest(BaseModel):
    symbol: str
    end_date: str
    period: Optional[str] = "1M"

class CombinedChartRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    chart_types: List[str] = ["price"]  # ["price", "moving_average", "volume"]
    ma_periods: Optional[List[int]] = [5, 20, 60]

@router.post("/stock-chart/price")
async def get_stock_price_chart(request: StockChartRequest):
    """
    주가 차트 데이터를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    - **chart_type**: 차트 타입 ("price", "volume", "candlestick")
    """
    try:
        result = StockChartService.get_price_chart(
            ticker=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            chart_type=request.chart_type
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/stock-chart/moving-average")
async def get_stock_ma_chart(request: StockChartRequest):
    """
    이동평균이 포함된 주가 차트 데이터를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    - **ma_periods**: 이동평균 기간 리스트 (예: [5, 20, 60])
    """
    try:
        result = StockChartService.get_ma_chart(
            ticker=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            ma_periods=request.ma_periods
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/stock-chart/period")
async def get_stock_period_chart(request: PeriodChartRequest):
    """
    기간별 주가 차트 데이터를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **end_date**: 기준일 (YYYY-MM-DD)
    - **period**: 기간 ("1W", "1M", "3M", "6M", "1Y")
    """
    try:
        result = StockChartService.get_period_chart(
            ticker=request.symbol,
            end_date=request.end_date,
            period=request.period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

@router.post("/stock-chart/combined")
async def get_combined_stock_chart(request: CombinedChartRequest):
    """
    여러 차트 타입을 조합한 주가 차트 데이터를 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    - **chart_types**: 차트 타입 리스트 (["price", "moving_average", "volume"])
    - **ma_periods**: 이동평균 기간 리스트 (예: [5, 20, 60])
    """
    try:
        result = StockChartService.get_combined_chart(
            ticker=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            chart_types=request.chart_types,
            ma_periods=request.ma_periods
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/stock-chart/moving-average-only")
async def get_moving_average_only(request: StockChartRequest):
    """
    이동평균 데이터만을 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    - **ma_periods**: 이동평균 기간 리스트 (예: [5, 20, 60])
    """
    try:
        result = StockChartService.get_moving_average_only(
            ticker=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            ma_periods=request.ma_periods
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/stock-chart/volume-only")
async def get_volume_only(request: StockChartRequest):
    """
    거래량 데이터만을 반환합니다.
    
    - **symbol**: 종목 코드 (예: "AAPL")
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD)
    """
    try:
        result = StockChartService.get_volume_only(
            ticker=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 간단한 GET 엔드포인트들 (쿼리 파라미터 사용)
@router.get("/stock-chart/quick-chart")
async def get_quick_stock_chart(
    symbol: str = Query(..., description="종목 코드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)"),
    chart_type: str = Query("price", description="차트 타입")
):
    """
    간단한 주가 차트 데이터를 반환합니다. (GET 방식)
    """
    try:
        result = StockChartService.get_price_chart(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date,
            chart_type=chart_type
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
    chart_types: str = Query("price", description="차트 타입들 (콤마로 구분: price,moving_average,volume)"),
    ma_periods: str = Query("5,20,60", description="이동평균 기간들 (콤마로 구분)")
):
    """
    여러 차트 타입을 조합한 주가 차트 데이터를 반환합니다. (GET 방식)
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

@router.get("/stock-chart/period-chart")
async def get_period_stock_chart(
    symbol: str = Query(..., description="종목 코드"),
    end_date: str = Query(..., description="기준일 (YYYY-MM-DD)"),
    period: str = Query("1M", description="기간")
):
    """
    기간별 주가 차트 데이터를 반환합니다. (GET 방식)
    """
    try:
        result = StockChartService.get_period_chart(
            ticker=symbol,
            end_date=end_date,
            period=period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")