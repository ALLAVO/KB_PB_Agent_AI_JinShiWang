# Pydantic 데이터 모델 for Report
from pydantic import BaseModel, Field
from typing import List, Optional
# from .company import CompanyInfo # 예시: 다른 스키마 참조
# from .prediction import PredictionResult # 예시: 다른 스키마 참조

class ReportBase(BaseModel):
    customer_id: int = Field(..., description="고객 ID")
    company_name: Optional[str] = Field(None, description="기업명")
    stock_symbol: Optional[str] = Field(None, description="주식 심볼")
    prediction_direction: Optional[str] = Field(None, description="예측 방향 (up/down)")
    prediction_probability: Optional[float] = Field(None, description="예측 확률")
    highlight_news: Optional[List[str]] = Field(None, description="주요 뉴스")

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    # 생성 날짜 등을 추가할 수 있습니다.
    # created_at: datetime

    class Config:
        orm_mode = True
