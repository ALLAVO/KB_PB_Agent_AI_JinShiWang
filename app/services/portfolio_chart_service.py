from sqlalchemy import create_engine, text
from app.core.config import settings
from typing import List, Dict, Optional
import logging
from collections import defaultdict
from openai import OpenAI


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

# 도넛 차트에 대한 고객 포트폴리오 데이터와 고객이 속한 유형의 데이터를 반환하는 함수
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


def generate_portfolio_comparison_prompt(client_name, risk_profile, client_portfolio, peer_portfolio):
    """
    고객의 실제 포트폴리오와 유사 성향 투자자의 평균 포트폴리오를 비교해,
    자연스러운 one-shot 요약문을 생성하도록 프롬프트를 구성합니다.
    """
    example = """
    예시:
    김재훈 고객님의 포트폴리오는 기술과 헬스케어 섹터에 높은 비중을 두고 있으며, 생활 필수품과 금융 섹터에도 일정 수준 분산되어 있어 안정성과 성장성 간의 균형이 잘 잡혀 있습니다. 
    유사한 투자 성향의 다른 고객들은 기술과 금융 외에도 소비재 및 에너지 섹터의 비중이 더 높은 편인데, 김재훈 고객님의 구성은 상대적으로 경기 민감도는 낮지만 방어적 성격이 강한 점이 특징입니다. 
    최근처럼 시장 변동성이 큰 시기에는 이러한 포트폴리오가 리스크 관리에 유리할 수 있으며, 현 시점에서는 구성을 유지하되 향후 경기 회복 흐름에 따라 소비재나 에너지 섹터의 점진적 편입을 고려해볼 수 있습니다.
    """

    prompt = f"""
    당신은 15년차 PB(Private Banker)이며, 포트폴리오 분석에 능력이 출중합니다.
    아래 고객님의 실제 포트폴리오와, 유사한 위험 성향을 가진 투자자들의 평균 포트폴리오를 비교해 주세요.

    목표는 고객의 현재 구성을 이해하기 쉽게 설명하고,
    유사 투자자와의 차이를 기반으로 전략적 조언을 제시하는 것입니다.
    문장은 자연스럽고 간결하게 연결된 한 편의 요약 형식으로 작성하세요.

    [고객 이름]: {client_name}
    [고객 투자 성향]: {risk_profile}

    [고객 포트폴리오 섹터 구성]
    {', '.join([f"{item['sector']} {item['percentage']}%" for item in client_portfolio])}

    [유사 투자자 평균 포트폴리오]
    {', '.join([f"{item['sector']} {item['percentage']}%" for item in peer_portfolio])}

    {example}

    이제 위 정보를 바탕으로 고객 맞춤 요약문을 작성해 주세요.
    """.strip()
    return prompt


def get_portfolio_chart_ai_summary(client_id: str) -> str:
    """
    고객의 포트폴리오와 추천 포트폴리오를 비교하여 AI 요약을 반환합니다.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    data = get_client_portfolio_chart_data(client_id)
    if "error" in data:
        return "포트폴리오 데이터를 불러올 수 없습니다."

    client_name = data.get("client_name", "")
    risk_profile = data.get("risk_profile", "")
    client_portfolio = data.get("client_portfolio", [])
    recommended_portfolio = data.get("recommended_portfolio", [])

    prompt = generate_portfolio_comparison_prompt(
        client_name, risk_profile, client_portfolio, recommended_portfolio
    )

    # OpenAI ChatCompletion API 올바른 사용법
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    summary = response.choices[0].message.content.strip()
    logger.info(f"AI summary generated for client {client_id}: {summary}")

    return summary
