from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.industry_agent.clustering import get_industry_top3_articles

router = APIRouter()

class IndustryRequest(BaseModel):
    sector: str
    start_date: str

@router.post("/top3_articles")
def get_industry_top3_articles_endpoint(request: IndustryRequest):
    """
    산업 섹터와 시작일을 받아 클러스터링 기반 상위 3개 기사를 반환합니다.
    """
    try:
        result = get_industry_top3_articles(request.sector, request.start_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing industry analysis: {str(e)}")
