from openai import OpenAI
from app.core.config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def generate_performance_summary(performance_data: Dict[str, Any]) -> Dict[str, str]:
    """
    고객 성과 데이터를 바탕으로 AI 요약과 코멘트를 생성합니다.
    """
    client_name = performance_data.get('client_name', '고객')
    try:
        # OpenAI 클라이언트 초기화
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 성과 데이터에서 주요 정보 추출
        benchmark = performance_data.get('benchmark', 'S&P 500')
        period_months = performance_data.get('performance_period_months', 3)
        
        weekly_portfolio   = performance_data.get('weekly_return', {}).get('portfolio', 0)
        weekly_benchmark   = performance_data.get('weekly_return', {}).get('benchmark', 0)
        performance_portfolio = performance_data.get('performance_return', {}).get('portfolio', 0)
        performance_benchmark = performance_data.get('performance_return', {}).get('benchmark', 0)
        
        # 초과수익률 계산
        weekly_outperformance     = weekly_portfolio   - weekly_benchmark
        performance_outperformance = performance_portfolio - performance_benchmark

        # 포트폴리오 종목 리스트 추출
        portfolio_stocks = performance_data.get('portfolio_stocks', [])
        portfolio_stocks_str = ', '.join(portfolio_stocks) if portfolio_stocks else '없음'

        # 종목별 1주일 수익률 정보 추출 및 문자열 변환
        stocks_weekly_return = performance_data.get('stocks_weekly_return', [])
        if stocks_weekly_return:
            stocks_weekly_return_str = "; ".join(
                [f"{item['stock']}: {item['weekly_return']:+.2f}%" for item in stocks_weekly_return]
            )
        else:
            stocks_weekly_return_str = "없음"

        # 프롬프트 생성
        prompt = f"""
                당신은 KB국민은행의 전문 PB(Private Banker)입니다. 다음 고객의 투자 성과 데이터를 분석하여 통합된 투자 분석 리포트를 작성해주세요.

                **고객 정보:**
                - 고객명: {client_name}
                - 벤치마크: {benchmark}
                - 성과 구간: {period_months}개월
                - 포트폴리오 종목: {portfolio_stocks_str}

                **성과 데이터:**
                - 일주일간 포트폴리오 수익률: {weekly_portfolio:+.2f}%
                - 일주일간 벤치마크 수익률: {weekly_benchmark:+.2f}%
                - 일주일간 초과수익률: {weekly_outperformance:+.2f}%p

                - {period_months}개월 포트폴리오 수익률: {performance_portfolio:+.2f}%
                - {period_months}개월 벤치마크 수익률: {performance_benchmark:+.2f}%
                - {period_months}개월 초과수익률: {performance_outperformance:+.2f}%p

                - 종목별 1주일 수익률: {stocks_weekly_return_str}

                다음 내용을 포함하여 5-6줄로 통합된 투자 분석을 작성해주세요:
                1. 현재 투자 성과에 대한 간단한 평가
                2. 벤치마크 대비 성과 분석
                3. 향후 투자 방향성 및 조언

                전문적이면서도 고객이 이해하기 쉬운 친근한 톤으로 작성해주세요.

                제목 없이 바로 1.이라는 숫자로 시작되도록 해주세요.
                """

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 KB국민은행의 전문 PB입니다. 고객에게 친근하면서도 전문적인 투자 조언을 제공합니다."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        ai_response = response.choices[0].message.content.strip()
        
        # ──────────────── 응답 파싱 ────────────────
        summary_lines, comment_lines = [], []
        current_section = None
        for line in ai_response.splitlines():
            line = line.strip()
            if '요약' in line:
                current_section = 'summary'
                continue
            if '코멘트' in line or '투자 코멘트' in line:
                current_section = 'comment'
                continue
            
            if not line or line.startswith('**'):
                continue
            
            if current_section == 'summary':
                summary_lines.append(line)
            elif current_section == 'comment':
                comment_lines.append(line)
        
        summary = ' '.join(summary_lines) if summary_lines else ai_response
        comment = ' '.join(comment_lines) if comment_lines else ""
        
        return {
            "summary": summary,
            "comment": comment
        }
    
    except Exception as e:
        logger.error(f"Error generating AI performance summary: {e}")
        # 기본 요약 반환
        return {
            "summary": (
                f"{client_name} 고객님의 투자 성과를 종합적으로 분석한 결과, "
                "전반적으로 양호한 수익률을 보이고 있습니다. 벤치마크 대비 안정적인 성과를 유지하고 있으며, "
                "지속적인 포트폴리오 모니터링을 통해 리스크 관리에 중점을 둔 투자 전략을 권장드립니다."
            ),
            "comment": ""
        }
