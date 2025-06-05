# 보고서 생성/조회 API 테스트 코드
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_get_report():
    # 고객 생성
    customer_data = {
        "name": "보고서고객",
        "pb_name": "PB보고서",
        "investment_propensity": "중립형"
    }
    cust_resp = client.post("/api/v1/customers/", json=customer_data)
    assert cust_resp.status_code in (200, 201)
    customer_id = cust_resp.json()["id"]

    # 보고서 생성
    report_req = {
        "customer_id": customer_id,
        "company_name": "Apple Inc.",
        "stock_symbol": "AAPL",
        "prediction_direction": "up",
        "prediction_probability": 0.85,
        "highlight_news": ["Apple releases new product", "Stock hits all-time high"]
    }
    report_resp = client.post("/api/v1/reports/", json=report_req)
    assert report_resp.status_code in (200, 201)
    report_data = report_resp.json()
    assert report_data["customer_id"] == customer_id
    assert report_data["company_name"] == "Apple Inc."
    assert report_data["prediction_direction"] == "up"
    assert report_data["prediction_probability"] == 0.85
    assert len(report_data["highlight_news"]) == 2

    # 보고서 조회
    report_id = report_data["id"]
    get_resp = client.get(f"/api/v1/reports/{report_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == report_id
    assert get_data["customer_id"] == customer_id
    assert get_data["company_name"] == "Apple Inc."

def test_end_to_end_report_flow():
    # 1. 고객 생성
    customer_data = {
        "name": "E2E고객",
        "pb_name": "E2EPB",
        "investment_propensity": "적극투자형",
        "investment_portfolio": [
            {"stock_symbol": "AAPL", "quantity": 10, "average_purchase_price": 190.0}
        ]
    }
    cust_resp = client.post("/api/v1/customers/", json=customer_data)
    assert cust_resp.status_code in (200, 201)
    customer_id = cust_resp.json()["id"]

    # 2. 예측 생성
    pred_req = {"customer_id": customer_id, "stock_symbol": "AAPL"}
    pred_resp = client.post("/api/v1/predictions/", json=pred_req)
    assert pred_resp.status_code in (200, 201)
    pred_data = pred_resp.json()
    assert pred_data["direction"] == "up"
    assert pred_data["probability"] == 0.75

    # 3. 보고서 생성 (company_name 없이 예측 결과 기반 자동 채움)
    report_req = {
        "customer_id": customer_id,
        "stock_symbol": "AAPL",
        # company_name, prediction_direction, prediction_probability는 omit
        "highlight_news": ["AAPL hits new high"]
    }
    report_resp = client.post("/api/v1/reports/", json=report_req)
    assert report_resp.status_code in (200, 201)
    report_data = report_resp.json()
    assert report_data["customer_id"] == customer_id
    assert report_data["stock_symbol"] == "AAPL"
    assert report_data["prediction_direction"] == "up"
    assert report_data["prediction_probability"] == 0.75
    assert report_data["highlight_news"] == ["AAPL hits new high"]

    # 4. 보고서 조회
    report_id = report_data["id"]
    get_resp = client.get(f"/api/v1/reports/{report_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == report_id
    assert get_data["customer_id"] == customer_id
    assert get_data["stock_symbol"] == "AAPL"
    assert get_data["prediction_direction"] == "up"
    assert get_data["prediction_probability"] == 0.75