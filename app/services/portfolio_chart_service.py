from sqlalchemy import create_engine, text
from app.core.config import settings
from typing import List, Dict, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

def get_database_connection():
    """데이터베이스 연결"""
    try:
        if hasattr(settings, 'USE_SUPABASE') and settings.USE_SUPABASE:
            database_url = settings.SUPABASE_DATABASE_URL
        else:
            database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        
        engine = create_engine(database_url, pool_pre_ping=True)
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_client_portfolio_chart_data(client_id: str) -> Dict:
    """고객의 포트폴리오 차트 데이터를 반환합니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            # 고객 기본 정보 및 위험성향 가져오기
            client_query = text("""
                SELECT name, risk_profile
                FROM virtual_clients_v4
                WHERE id = :client_id
            """)
            client_result = conn.execute(client_query, {"client_id": client_id})
            client_row = client_result.fetchone()
            
            if not client_row:
                return {"error": f"Client with id {client_id} not found"}
            
            client_name = client_row[0]
            risk_profile = client_row[1]
            
            # 고객 포트폴리오 가져오기 (섹터별 수량 포함)
            portfolio_query = text("""
                SELECT stock, quantity, sector
                FROM virtual_clients_portfolio
                WHERE id = :client_id
                ORDER BY stock
            """)
            portfolio_result = conn.execute(portfolio_query, {"client_id": client_id})
            
            # 섹터별 비중 계산
            sector_quantities = defaultdict(int)
            total_quantity = 0
            
            for row in portfolio_result:
                stock, quantity, sector = row
                if quantity and sector:
                    sector_quantities[sector] += quantity
                    total_quantity += quantity
            
            # 고객 포트폴리오 섹터 분포 계산
            client_portfolio_data = []
            for sector, quantity in sector_quantities.items():
                if total_quantity > 0:
                    percentage = (quantity / total_quantity) * 100
                    client_portfolio_data.append({
                        "sector": sector,
                        "percentage": round(percentage, 1),
                        "quantity": quantity
                    })
            
            # 비중 순으로 정렬
            client_portfolio_data.sort(key=lambda x: x['percentage'], reverse=True)
            
            # 위험성향에 따른 추천 포트폴리오 가져오기 - 한글 컬럼명 직접 사용
            risk_profile_korean = {
                'Conservative': '안정형',
                'Very Conservative': '안정형',
                'Moderate': '중립형',
                'Aggressive': '적극형',
                'Very Aggressive': '적극형'
            }
            
            korean_profile = risk_profile_korean.get(risk_profile, '중립형')
            
            recommended_query = text(f"""
                SELECT sector, "{korean_profile}"
                FROM sector_portfolio
                ORDER BY "{korean_profile}" DESC
            """)
            recommended_result = conn.execute(recommended_query)
            
            recommended_portfolio_data = []
            for row in recommended_result:
                sector, percentage = row
                if percentage and percentage > 0:
                    recommended_portfolio_data.append({
                        "sector": sector,
                        "percentage": round(float(percentage), 1)
                    })
            
            return {
                "client_name": client_name,
                "risk_profile": risk_profile,
                "client_portfolio": client_portfolio_data,
                "recommended_portfolio": recommended_portfolio_data,
                "portfolio_summary": {
                    "total_sectors": len(client_portfolio_data),
                    "total_quantity": total_quantity
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching portfolio chart data for client {client_id}: {e}")
        raise

def get_risk_profile_info(risk_profile: str) -> Dict:
    """위험성향에 대한 정보를 반환합니다."""
    profiles = {
        'Conservative': {
            'label': '안정형',
            'description': '안정적인 수익을 추구하는 투자성향',
            'color': '#7BA05B',
            'korean_name': '안정형'
        },
        'Very Conservative': {
            'label': '매우안정형',
            'description': '위험을 최소화하는 투자성향',
            'color': '#8B7355',
            'korean_name': '매우안정형'
        },
        'Moderate': {
            'label': '중립형',
            'description': '적절한 위험을 감수하는 투자성향',
            'color': '#D4B96A',
            'korean_name': '중립형'
        },
        'Aggressive': {
            'label': '적극형',
            'description': '높은 수익을 위해 위험을 감수하는 투자성향',
            'color': '#C4756E',
            'korean_name': '적극형'
        },
        'Very Aggressive': {
            'label': '매우적극형',
            'description': '최고 수익을 위해 높은 위험을 감수하는 투자성향',
            'color': '#6D5A42',
            'korean_name': '매우적극형'
        }
    }
    return profiles.get(risk_profile, {
        'label': risk_profile,
        'description': '',
        'color': '#666',
        'korean_name': risk_profile
    })
