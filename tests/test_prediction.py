import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_prediction():
    # 고객 먼저 생성
    customer_data = {
        "name": "예측고객",
        "pb_name": "PB예측",
        "investment_propensity": "공격투자형"
    }
    cust_resp = client.post("/api/v1/customers/", json=customer_data)
    assert cust_resp.status_code in (200, 201)
    customer_id = cust_resp.json()["id"]

    # 예측 요청
    pred_req = {
        "customer_id": customer_id,
        "stock_symbol": "AAPL"
    }
    pred_resp = client.post("/api/v1/predictions/", json=pred_req)
    assert pred_resp.status_code in (200, 201)
    pred_data = pred_resp.json()
    assert pred_data["customer_id"] == customer_id
    assert pred_data["stock_symbol"] == "AAPL"
    assert pred_data["direction"] in ("up", "down")
    assert 0.5 <= pred_data["probability"] <= 1.0

    # 예측 결과 조회
    pred_id = pred_data["prediction_id"]
    get_resp = client.get(f"/api/v1/predictions/{pred_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["prediction_id"] == pred_id
    assert get_data["customer_id"] == customer_id
    assert get_data["stock_symbol"] == "AAPL"
