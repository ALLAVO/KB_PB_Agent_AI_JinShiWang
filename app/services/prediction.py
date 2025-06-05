from app.schemas.prediction import PredictionResult, PredictionRequest

def run_prediction(request: PredictionRequest, prediction_id: int) -> PredictionResult:
    # 임시 mock: 항상 상승(up), 확률 0.75로 고정 반환
    return PredictionResult(
        prediction_id=prediction_id,
        customer_id=request.customer_id,
        stock_symbol=request.stock_symbol,
        direction="up",
        probability=0.75
    )