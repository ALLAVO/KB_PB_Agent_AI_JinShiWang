from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# 투자 포트폴리오의 개별 항목을 위한 모델
class PortfolioItemBase(BaseModel):
    stock_symbol: str = Field(..., description="주식 심볼 (예: AAPL, TSLA)")
    quantity: int = Field(..., gt=0, description="보유 수량 (0보다 커야 함)")
    average_purchase_price: Optional[float] = Field(None, gt=0, description="평균 매수 단가 (선택 사항)")

class PortfolioItemCreate(PortfolioItemBase):
    pass

class PortfolioItem(PortfolioItemBase):
    id: int # DB에서 자동 생성되는 ID
    owner_id: int # 어떤 고객의 포트폴리오 항목인지 식별하기 위한 FK (Customer ID)

    model_config = ConfigDict(from_attributes=True) # orm_mode -> from_attributes

# 고객 정보 모델
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, description="고객 성함")
    pb_name: str = Field(..., min_length=1, description="담당 PB 성함")
    investment_propensity: Optional[str] = Field(None, description="고객 투자 성향 (예: 위험 중립형, 공격투자형 등)")
    investment_portfolio: Optional[List[PortfolioItemBase]] = Field(None, description="고객 투자 포트폴리오 목록")

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int # DB에서 자동 생성되는 ID
    investment_portfolio: Optional[List[PortfolioItem]] = Field(None, description="고객 투자 포트폴리오 목록 (DB에서 조회 시 ID 포함)")

    model_config = ConfigDict(from_attributes=True)