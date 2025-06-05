# Pydantic 데이터 모델 for Company
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict

class KeyExecutive(BaseModel):
    name: str
    title: str
    pay: Optional[str] = None

class FinancialStatement(BaseModel):
    period: str
    data: Dict[str, float]

class CompanyInfoBase(BaseModel):
    # Yahoo Finance에서 가져올 기업 정보 필드들
    company_name: str = Field(..., description="기업명")
    stock_symbol: str = Field(..., description="티커 심볼")
    industry: Optional[str] = Field(None, description="산업")
    sector: Optional[str] = Field(None, description="섹터")
    business_summary: Optional[str] = Field(None, description="기업 설명")
    website: Optional[str] = Field(None, description="웹사이트")
    address: Optional[str] = Field(None, description="주소")
    phone: Optional[str] = Field(None, description="전화번호")
    employees: Optional[int] = Field(None, description="임직원 수")
    key_executives: Optional[List[KeyExecutive]] = Field(None, description="주요 경영진")
    income_statements: Optional[List[FinancialStatement]] = Field(None, description="손익계산서")
    balance_sheets: Optional[List[FinancialStatement]] = Field(None, description="재무상태표")
    cashflow_statements: Optional[List[FinancialStatement]] = Field(None, description="현금흐름표")
    key_ratios: Optional[Dict[str, float]] = Field(None, description="주요 재무 비율")

class CompanyInfoCreate(CompanyInfoBase):
    pass

class CompanyInfo(CompanyInfoBase):
    model_config = ConfigDict(from_attributes=True)
