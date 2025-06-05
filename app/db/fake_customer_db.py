# 임시 고객 DB (Fake DB)
# 실제 DB로 교체 시 이 파일만 삭제/교체하면 됩니다.
from typing import List
from app.schemas.customer import Customer

fake_customers_db: List[Customer] = []
customer_id_seq = 1
portfolio_id_seq = 1

def get_fake_customers_db():
    return fake_customers_db

def get_customer_id_seq():
    global customer_id_seq
    return customer_id_seq

def increment_customer_id_seq():
    global customer_id_seq
    customer_id_seq += 1
    return customer_id_seq - 1

def get_portfolio_id_seq():
    global portfolio_id_seq
    return portfolio_id_seq

def increment_portfolio_id_seq():
    global portfolio_id_seq
    portfolio_id_seq += 1
    return portfolio_id_seq - 1
