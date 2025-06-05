# 주가 예측 관련 API
from fastapi import APIRouter, HTTPException

from app.db.fake_prediction_db import get_fake_predictions_db, increment_prediction_id_seq
from app.schemas.prediction import PredictionRequest, PredictionResult
from app.services.prediction import run_prediction

router = APIRouter()


@router.post("/predictions/", response_model=PredictionResult)
def create_prediction(request: PredictionRequest):
    prediction_id = increment_prediction_id_seq()
    result = run_prediction(request, prediction_id)
    get_fake_predictions_db().append(result)
    return result


@router.get("/predictions/{prediction_id}", response_model=PredictionResult)
def get_prediction(prediction_id: int):
    for pred in get_fake_predictions_db():
        if pred.prediction_id == prediction_id:
            return pred
    raise HTTPException(status_code=404, detail="Prediction not found")