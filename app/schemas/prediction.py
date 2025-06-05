# Pydantic 데이터 모델 for Prediction
from pydantic import BaseModel, Field
from typing import Optional

class PredictionRequest(BaseModel):
    customer_id: int = Field(..., description="고객 ID")
    stock_symbol: str = Field(..., description="예측할 주식 심볼")
    # 필요시 추가 입력 필드

class PredictionResult(BaseModel):
    prediction_id: int = Field(..., description="예측 결과 ID")
    customer_id: int
    stock_symbol: str
    direction: str = Field(..., description="예측 방향 (up/down)")
    probability: float = Field(..., ge=0, le=1, description="상승 확률 (0~1)")
    # 필요시 추가 결과 필드
