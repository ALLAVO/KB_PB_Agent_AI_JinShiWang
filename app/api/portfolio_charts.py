from fastapi import APIRouter, HTTPException
from app.services.portfolio_chart_service import get_client_portfolio_chart_data, get_risk_profile_info
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/clients/{client_id}/portfolio-chart")
def get_client_portfolio_chart(client_id: str):
    """고객의 포트폴리오 차트 데이터를 반환합니다."""
    try:
        chart_data = get_client_portfolio_chart_data(client_id)
        
        if "error" in chart_data:
            raise HTTPException(status_code=404, detail=chart_data["error"])
        
        # 위험성향 정보 추가
        risk_profile_info = get_risk_profile_info(chart_data["risk_profile"])
        chart_data["risk_profile_info"] = risk_profile_info
        
        return chart_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio chart for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
