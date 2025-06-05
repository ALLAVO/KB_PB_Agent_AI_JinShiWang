# 고객 정보 입력/조회 API
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.customer import Customer, CustomerCreate, PortfolioItem, PortfolioItemCreate
from app.db.fake_customer_db import (
    get_fake_customers_db,
    get_customer_id_seq,
    increment_customer_id_seq,
    get_portfolio_id_seq,
    increment_portfolio_id_seq
)

router = APIRouter()  # 경로를 모듈화하고 관리하기 위한 라우터 생성

@router.post("/customers/", response_model=Customer)
def create_customer(customer: CustomerCreate):
    # 중복 고객(이름+PB) 방지
    for existing in get_fake_customers_db():
        if existing.name == customer.name and existing.pb_name == customer.pb_name:
            raise HTTPException(status_code=409, detail="이미 동일한 이름과 PB의 고객이 존재합니다.")
    # 포트폴리오 항목에 id 부여
    portfolio_items = []
    customer_id = increment_customer_id_seq()
    if customer.investment_portfolio:
        for item in customer.investment_portfolio:
            portfolio_items.append(
                PortfolioItem(
                    id=increment_portfolio_id_seq(),
                    owner_id=customer_id,
                    **item.model_dump()  # .dict() -> .model_dump() for Pydantic v2
                )
            )
    new_customer = Customer(
        id=customer_id,
        name=customer.name,
        pb_name=customer.pb_name,
        investment_propensity=customer.investment_propensity,
        investment_portfolio=portfolio_items if portfolio_items else None
    )
    get_fake_customers_db().append(new_customer)
    return new_customer

@router.get("/customers/", response_model=List[Customer])
def list_customers():
    return get_fake_customers_db()

@router.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    for customer in get_fake_customers_db():
        if customer.id == customer_id:
            return customer
    raise HTTPException(status_code=404, detail="Customer not found")

@router.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: CustomerCreate):
    db = get_fake_customers_db()
    for idx, existing in enumerate(db):
        if existing.id == customer_id:
            # 중복 방지(본인 제외)
            for other in db:
                if other.id != customer_id and other.name == customer.name and other.pb_name == customer.pb_name:
                    raise HTTPException(status_code=409, detail="이미 동일한 이름과 PB의 고객이 존재합니다.")
            # 포트폴리오 재생성
            portfolio_items = []
            if customer.investment_portfolio:
                for item in customer.investment_portfolio:
                    portfolio_items.append(
                        PortfolioItem(
                            id=increment_portfolio_id_seq(),
                            owner_id=customer_id,
                            **item.model_dump()
                        )
                    )
            updated = Customer(
                id=customer_id,
                name=customer.name,
                pb_name=customer.pb_name,
                investment_propensity=customer.investment_propensity,
                investment_portfolio=portfolio_items if portfolio_items else None
            )
            db[idx] = updated
            return updated
    raise HTTPException(status_code=404, detail="Customer not found")

@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int):
    db = get_fake_customers_db()
    for idx, customer in enumerate(db):
        if customer.id == customer_id:
            del db[idx]
            return
    raise HTTPException(status_code=404, detail="Customer not found")