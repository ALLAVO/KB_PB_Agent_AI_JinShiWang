# 기업 정보 관련 API
from fastapi import APIRouter, HTTPException

from app.schemas.company import CompanyInfo
from app.services.crawler import get_company_info_from_yahoo

router = APIRouter()

@router.get("/companies/{stock_symbol}", response_model=CompanyInfo)
def get_company_info(stock_symbol: str):
    data = get_company_info_from_yahoo(stock_symbol)
    if not data.get("company_name") or "정보 없음" in data["company_name"]:
        raise HTTPException(status_code=404, detail="해당 기업 정보를 찾을 수 없습니다.")
    return data