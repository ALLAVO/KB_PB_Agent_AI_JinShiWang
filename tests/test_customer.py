# 고객 정보 API 테스트 코드
from fastapi.testclient import TestClient
from app.main import app # FastAPI app 임포트
from app.schemas.customer import CustomerCreate, Customer

client = TestClient(app)

def test_create_customer():
    customer_data = {
        "name": "테스트 고객", 
        "pb_name": "테스트 PB", 
        "investment_propensity": "공격투자형"
    }
    response = client.post("/api/v1/customers/", json=customer_data) # API 엔드포인트는 실제 설정에 맞게 수정
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert "id" in data

def test_create_customer_with_portfolio():
    customer_data = {
        "name": "포트폴리오 고객",
        "pb_name": "PB2",
        "investment_propensity": "적극투자형",
        "investment_portfolio": [
            {
                "stock_symbol": "TSLA",
                "quantity": 10,
                "average_purchase_price": 80000.0
            },
            {
                "stock_symbol": "AAPL",
                "quantity": 5,
                "average_purchase_price": 190.5
            }
        ]
    }
    response = client.post("/api/v1/customers/", json=customer_data)
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert "investment_portfolio" in data
    assert isinstance(data["investment_portfolio"], list)
    assert len(data["investment_portfolio"]) == 2
    assert data["investment_portfolio"][0]["stock_symbol"] == "TSLA"
    assert data["investment_portfolio"][1]["stock_symbol"] == "AAPL"
    assert data["investment_portfolio"][0]["quantity"] == 10
    assert data["investment_portfolio"][1]["average_purchase_price"] == 190.5

def test_list_customers():
    response = client.get("/api/v1/customers/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 최소 한 명 이상의 고객이 있어야 함 (이전에 생성된 고객)
    assert any(c["name"] == "테스트 고객" for c in data)

def test_get_customer():
    # 우선 고객을 하나 생성
    customer_data = {
        "name": "조회 고객",
        "pb_name": "PB1",
        "investment_propensity": "안정형"
    }
    create_resp = client.post("/api/v1/customers/", json=customer_data)
    assert create_resp.status_code == 200 or create_resp.status_code == 201
    customer_id = create_resp.json()["id"]
    # 해당 고객 조회
    get_resp = client.get(f"/api/v1/customers/{customer_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == customer_id
    assert data["name"] == customer_data["name"]

# # 여기에 다른 고객 관련 테스트 함수들을 추가합니다.
pass