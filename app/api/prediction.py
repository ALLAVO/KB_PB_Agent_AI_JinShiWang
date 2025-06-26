from fastapi import APIRouter, Query, Body
from pydantic import BaseModel
from app.services.prediction import get_prediction_summary

router = APIRouter()

class PredictionSummaryRequest(BaseModel):
    stock_symbol: str
    start_date: str
    end_date: str

@router.post(
    "/prediction/summary",
    summary="입력된 기업의 다음주 주가 전망 예측 요약 조회",
    description="주식 심볼, 시작일, 종료일을 입력받아 해당 기간 내 예측 요약 정보를 반환합니다. ",
    tags=["article analyze"]
)
def prediction_summary(
    request: PredictionSummaryRequest = Body(
        ...,
        example={
            "stock_symbol": "GS",
            "start_date": "2023-12-10",
            "end_date": "2023-12-16"
        },
        description="예측 요약 요청. stock_symbol: 종목 코드(GS), start_date: 시작일(2023-12-11), end_date: 종료일(2023-12-14)"
    )
):
    summary = get_prediction_summary(
        request.stock_symbol,
        request.start_date,
        request.end_date
    )
    return {"summary": summary}
