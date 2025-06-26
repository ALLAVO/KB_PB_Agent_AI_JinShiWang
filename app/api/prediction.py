from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.prediction import get_prediction_summary

router = APIRouter()

class PredictionSummaryRequest(BaseModel):
    stock_symbol: str
    start_date: str
    end_date: str

@router.post("/prediction/summary")
def prediction_summary(
    request: PredictionSummaryRequest = Query(
        ...,
        description="예측 요약 요청. stock_symbol: 종목 코드(GS), start_date: 시작일(2023-12-11), end_date: 종료일(2023-12-14)"
    )
):
    summary = get_prediction_summary(
        request.stock_symbol,
        request.start_date,
        request.end_date
    )
    return {"summary": summary}
