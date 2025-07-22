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
                당신은 15년차 전문적인 PB(Private Banker)입니다. 다음 고객의 투자 성과 데이터를 분석하여 통합된 투자 분석 리포트를 작성해주세요.

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

                1. 개괄적 투자 평가 서두
                    - 고객님의 지난 {period_months}개월간의 운용을, 전략의 일관성과 실행력이 반영된 결과로 평가하는 문장으로 시작해주세요.  
                    - 이 문장은 수익률이 좋든 나쁘든 모두 사용할 수 있도록 **중립적이고 전문적인 어조**로 작성해주세요.  
                    예: "김재훈 고객님의 지난 11개월간 운용은, 단기 흐름에 흔들리지 않고 일관된 투자 철학을 유지해온 결과입니다."

                2. **성과 평가**:  
                    다음 조건에 따라 해당하는 문장을 작성해주세요. 담백하고 신뢰감 있는 표현을 사용해주세요.

                    - 포트폴리오 수익률이 양수이고 초과수익률도 양수인 경우:  
                    "리밸런싱 이후 누적 수익률은 +{performance_portfolio:.2f}%로, 벤치마크(+{performance_benchmark:.2f}%)를 상회했습니다. 정말 잘 하셨습니다. 시장을 이기기란 쉽지 않은데, 멋진 결과입니다."

                    - 포트폴리오 수익률이 양수이고 초과수익률은 음수인 경우:  
                    "리밸런싱 이후 누적 수익률은 +{performance_portfolio:.2f}%로 자체 성과는 괜찮았지만, 벤치마크(+{performance_benchmark:.2f}%)에는 못 미쳤습니다. 시장 수익률을 따라가지 못한 점은 아쉽습니다."

                    - 포트폴리오 수익률이 음수이고 초과수익률은 양수인 경우:  
                    "리밸런싱 이후 누적 수익률은 -{performance_portfolio:.2f}%였지만, 벤치마크(-{performance_benchmark:.2f}%)보다 낙폭이 적었습니다. 쉽지 않은 시장에서 선방하셨다고 평가할 수 있습니다."

                    - 포트폴리오 수익률이 음수이고 초과수익률도 음수인 경우:  
                    "리밸런싱 이후 누적 수익률은 -{performance_portfolio:.2f}%로 부진했고, 벤치마크(-{performance_benchmark:.2f}%)보다도 낮았습니다. 이번엔 우리의 전략이 유효하지 않았던 것 같습니다. 아쉬운 구간입니다."

                3. **단기 흐름 및 종목 기여도 평가**  
                    - 최근 1주일간 포트폴리오 수익률과 벤치마크 수익률을 비교하여 단기 흐름을 평가해 주세요.  
                    예: "최근 1주일간 수익률은 +2.45%로 벤치마크(+1.35%)를 상회하며 단기적으로도 긍정적인 흐름입니다."  
                    - `{stocks_weekly_return_str}` 중 가장 높은 수익률과 가장 낮은 수익률을 기록한 종목을 언급하고, 그 영향을 간결하게 정리해 주세요.  
                    예: "AVGO는 +8.1% 상승하며 가장 큰 기여를 했고, KO는 -2.0% 하락해 수익에 다소 부담을 주었습니다."

                4. **향후 조언**:  
                    - 성과가 양호할 경우: “성과가 잘 나타난 만큼, 이제는 리스크 관리와 분산 전략에 집중할 시점입니다.”
                    - 성과가 부진할 경우: “성과가 아쉬운 만큼, 다음 기회를 준비하기 위한 조정이 필요해 보입니다.”

                5. **마무리**:  
                    다음 문장으로 마무리해주세요:  
                    "성과를 함께 돌아보고, 다음 방향을 함께 고민해드리겠습니다. 언제든 편하게 상담 요청 주세요."


                전문적이면서도 고객이 이해하기 쉬운 친근한 톤으로 작성해주세요.

                출력 결과에서는 각 항목 앞에 1. 2. 3. 등의 숫자만 붙이고, 항목 제목은 생략해 주세요.  
                모든 내용은 하나의 리포트처럼 자연스럽게 이어지되, 각 문단을 구분하기 위해 숫자만 붙여 주세요.
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
