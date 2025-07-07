from fastapi import APIRouter, HTTPException, Path
from typing import List, Dict
from app.services.client_services import get_all_clients, get_client_by_id, get_client_portfolio, get_client_summary
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
async def fetch_client_detail(client_id: int = Path(..., description="고객 ID")):
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
async def fetch_client_portfolio(client_id: int = Path(..., description="고객 ID")):
    """특정 고객의 포트폴리오를 반환합니다."""
    try:
        portfolio = get_client_portfolio(client_id)
        return portfolio
    except Exception as e:
        logger.error(f"Error in fetch_client_portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/clients/{client_id}/summary", response_model=Dict)
async def fetch_client_summary(client_id: int = Path(..., description="고객 ID")):
    """특정 고객의 종합 정보를 반환합니다."""
    try:
        summary = get_client_summary(client_id)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch_client_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
