# 임시 예측 결과 저장소 및 시퀀스
from typing import List
from app.schemas.prediction import PredictionResult

fake_predictions_db: List[PredictionResult] = []
prediction_id_seq = 1

def get_fake_predictions_db():
    return fake_predictions_db

def increment_prediction_id_seq():
    global prediction_id_seq
    prediction_id_seq += 1
    return prediction_id_seq - 1
