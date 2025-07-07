from sqlalchemy import create_engine, text
from app.core.config import settings
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

def get_database_connection():
    """데이터베이스 연결"""
    try:
        if hasattr(settings, 'USE_SUPABASE') and settings.USE_SUPABASE:
            # Supabase 연결
            database_url = settings.SUPABASE_DATABASE_URL
        else:
            # 로컬 PostgreSQL 연결
            database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        
        engine = create_engine(database_url, pool_pre_ping=True)
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def parse_amount_string(amount_str: str) -> float:
    """
    '약 70억원', '50만원' 같은 문자열을 숫자로 변환합니다.
    """
    if not amount_str or amount_str in ('', 'null', 'NULL', None):
        return 0.0
    
    # 문자열이 이미 숫자인 경우
    try:
        return float(amount_str)
    except (ValueError, TypeError):
        pass
    
    # 한국어 단위가 포함된 문자열 파싱
    amount_str = str(amount_str).strip()
    
    # 숫자와 단위를 추출하는 정규식
    # 예: '약 70억원' -> '70', '억'
    pattern = r'(?:약\s*)?(\d+(?:\.\d+)?)\s*(억|만|천)?원?'
    match = re.search(pattern, amount_str)
    
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        
        # 단위에 따른 곱셈
        if unit == '억':
            return number * 100000000  # 1억 = 100,000,000
        elif unit == '만':
            return number * 10000      # 1만 = 10,000
        elif unit == '천':
            return number * 1000       # 1천 = 1,000
        else:
            return number              # 단위 없음
    
    # 파싱 실패시 0 반환
    logger.warning(f"Could not parse amount string: {amount_str}")
    return 0.0

def get_all_clients() -> List[Dict]:
    """모든 고객 정보를 가져옵니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            query = text("""
                SELECT id, name, sex, age, risk_profile, investment_horizon, total_amount
                FROM virtual_clients_v4
                ORDER BY id
            """)
            result = conn.execute(query)
            clients = []
            for row in result:
                # total_amount를 안전하게 변환
                try:
                    total_amount = parse_amount_string(row[6])
                except Exception as e:
                    logger.warning(f"Error parsing total_amount for client {row[0]}: {row[6]}, error: {e}")
                    total_amount = 0.0
                
                clients.append({
                    "id": row[0],
                    "name": row[1],
                    "sex": row[2],
                    "age": row[3],
                    "risk_profile": row[4],
                    "investment_horizon": row[5],
                    "total_amount": total_amount
                })
            return clients
    except Exception as e:
        logger.error(f"Error fetching all clients: {e}")
        raise

def get_client_by_id(client_id: int) -> Optional[Dict]:
    """특정 고객의 상세 정보를 가져옵니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            query = text("""
                SELECT id, name, sex, age, risk_profile, investment_horizon, 
                       total_amount, memo1, memo2, memo3
                FROM virtual_clients_v4
                WHERE id = :client_id
            """)
            result = conn.execute(query, {"client_id": client_id})
            row = result.fetchone()
            
            if row:
                # total_amount를 안전하게 변환
                try:
                    total_amount = parse_amount_string(row[6])
                except Exception as e:
                    logger.warning(f"Error parsing total_amount for client {client_id}: {row[6]}, error: {e}")
                    total_amount = 0.0
                
                return {
                    "id": row[0],
                    "name": row[1],
                    "sex": row[2],
                    "age": row[3],
                    "risk_profile": row[4],
                    "investment_horizon": row[5],
                    "total_amount": total_amount,
                    "memo1": row[7],
                    "memo2": row[8],
                    "memo3": row[9]
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching client {client_id}: {e}")
        raise

def get_client_portfolio(client_id: int) -> List[Dict]:
    """특정 고객의 포트폴리오 정보를 가져옵니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            query = text("""
                SELECT stock, quantity, sector
                FROM virtual_clients_portfolio
                WHERE id = :client_id
                ORDER BY stock
            """)
            result = conn.execute(query, {"client_id": client_id})
            portfolio = []
            for row in result:
                portfolio.append({
                    "stock": row[0],
                    "quantity": int(row[1]) if row[1] else 0,
                    "sector": row[2]
                })
            return portfolio
    except Exception as e:
        logger.error(f"Error fetching portfolio for client {client_id}: {e}")
        raise

def get_client_summary(client_id: int) -> Dict:
    """고객의 종합 정보 (기본정보 + 포트폴리오)를 가져옵니다."""
    try:
        client_info = get_client_by_id(client_id)
        if not client_info:
            return {"error": f"Client with id {client_id} not found"}
        
        portfolio = get_client_portfolio(client_id)
        
        # 포트폴리오 요약 계산
        total_stocks = len(portfolio)
        sectors = list(set([item["sector"] for item in portfolio if item["sector"]]))
        total_quantity = sum([item["quantity"] for item in portfolio])
        
        return {
            "client_info": client_info,
            "portfolio": portfolio,
            "portfolio_summary": {
                "total_stocks": total_stocks,
                "sectors": sectors,
                "total_quantity": total_quantity
            }
        }
    except Exception as e:
        logger.error(f"Error fetching client summary for {client_id}: {e}")
        raise
