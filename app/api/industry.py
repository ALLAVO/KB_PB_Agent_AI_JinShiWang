from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.clustering import get_industry_top3_articles
from app.services.industry_analysis import get_industry_top10_companies

router = APIRouter()

class IndustryRequest(BaseModel):
    sector: str
    start_date: str

class IndustryCompaniesRequest(BaseModel):
    sector: str
    end_date: str

@router.post("/industry/top3_articles")
def get_industry_top3_articles_endpoint(request: IndustryRequest):
    """
    산업 섹터와 시작일을 받아 클러스터링 기반 상위 3개 기사를 반환합니다.
    """
    try:
        result = get_industry_top3_articles(request.sector, request.start_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing industry analysis: {str(e)}")

@router.post("/industry/top10_companies")
def get_industry_top10_companies_endpoint(request: IndustryCompaniesRequest):
    """
    산업 섹터와 종료일을 받아 시가총액 상위 10개 기업 정보를 반환합니다.
    """
    try:
        result = get_industry_top10_companies(request.sector, request.end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing industry companies analysis: {str(e)}")
