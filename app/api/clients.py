from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Dict
from app.services.client_services import get_all_clients, get_client_by_id, get_client_portfolio, get_client_summary, get_client_performance_analysis
from app.core.config import settings
from app.services.portfolio_chart_service import get_portfolio_chart_ai_summary
from openai import OpenAI
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/clients", response_model=List[Dict])
async def fetch_all_clients():
    """모든 고객 목록을 반환합니다."""
    try:
        clients = get_all_clients()
        return clients
    except Exception as e:
        logger.error(f"Error in fetch_all_clients: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/clients/{client_id}", response_model=Dict)
async def fetch_client_detail(client_id: str = Path(..., description="고객 ID")):
    """특정 고객의 상세 정보를 반환합니다."""
    try:
        client = get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client with id {client_id} not found")
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch_client_detail: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/clients/{client_id}/portfolio", response_model=List[Dict])
async def fetch_client_portfolio(client_id: str = Path(..., description="고객 ID")):
    """특정 고객의 포트폴리오를 반환합니다."""
    try:
        portfolio = get_client_portfolio(client_id)
        return portfolio
    except Exception as e:
        logger.error(f"Error in fetch_client_portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/clients/{client_id}/summary", response_model=Dict)
async def fetch_client_summary(
    client_id: str = Path(..., description="고객 ID"),
    period_end_date: str = Query(None, description="기준 날짜 (YYYY-MM-DD)")
):
    """특정 고객의 종합 정보를 반환합니다."""
    try:
        summary = get_client_summary(client_id, period_end_date)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch_client_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/clients/{client_id}/performance/{period_end_date}", response_model=Dict)
async def fetch_client_performance(
    client_id: str = Path(..., description="고객 ID"),
    period_end_date: str = Path(..., description="기준 날짜 (YYYY-MM-DD)")
):
    """특정 고객의 성과 분석을 반환합니다."""
    try:
        performance = get_client_performance_analysis(client_id, period_end_date)
        if "error" in performance:
            raise HTTPException(status_code=404, detail=performance["error"])
        return performance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch_client_performance: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/clients/{client_id}/portfolio-chart-ai-summary", response_model=Dict)
async def fetch_client_portfolio_chart_ai_summary(client_id: str = Path(..., description="고객 ID")):
    """
    고객의 포트폴리오와 추천 포트폴리오 비교 AI 요약을 반환합니다.
    """
    try:
        # .env에서 OPENAI_API_KEY를 읽어 OpenAIClient 인스턴스 생성
        summary = get_portfolio_chart_ai_summary(client_id)
        return {"ai_summary": summary}
    except Exception as e:
        logger.error(f"Error in fetch_client_portfolio_chart_ai_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
