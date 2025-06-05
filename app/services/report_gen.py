from app.db.fake_customer_db import get_fake_customers_db
from app.db.fake_prediction_db import get_fake_predictions_db
from app.schemas.customer import Customer
from app.schemas.prediction import PredictionResult
from fastapi import HTTPException
from app.schemas.report import ReportCreate, Report

def generate_report(report_id: int, data: ReportCreate) -> Report:
    # 고객 정보 참조
    customer = next((c for c in get_fake_customers_db() if c.id == data.customer_id), None)
    if not customer:
        raise HTTPException(status_code=404, detail="고객 정보를 찾을 수 없습니다.")
    # 예측 결과 참조 (stock_symbol까지 일치)
    prediction = next((p for p in get_fake_predictions_db() if p.customer_id == data.customer_id and p.stock_symbol == data.stock_symbol), None)
    # 실제로는 기업 정보도 참조할 수 있음 (여기서는 company_name, stock_symbol만 사용)
    return Report(
        id=report_id,
        customer_id=data.customer_id,
        company_name=data.company_name or (customer.investment_portfolio[0].stock_symbol if customer.investment_portfolio else None),
        stock_symbol=data.stock_symbol or (prediction.stock_symbol if prediction else None),
        prediction_direction=data.prediction_direction or (prediction.direction if prediction else None),
        prediction_probability=data.prediction_probability or (prediction.probability if prediction else None),
        highlight_news=data.highlight_news
    )
