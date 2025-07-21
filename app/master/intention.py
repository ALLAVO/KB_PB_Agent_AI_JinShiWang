import os
import openai
import json
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# API 키 (환경변수 우선)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Intent 메타 정보
INTENTS = {
    "market":     "시황 Agent: ① 지수·환율 조회 ② 전주 Hot 기사 요약·키워드·감성",
    "enterprise": "기업정보 Agent: ① 재무제표·지표 조회 ② 주가 전망 예측/근거 제시 ③ 관련 기사 요약·키워드·감성",
    "industry":   "산업정보 Agent: ① 산업군 동향 파악 ② 대표 종목 추천 ③ 추천 종목 관련 기사 요약·키워드·감성",
    "personal":   "고객정보 Agent: ① 고객 기본 정보 조회 ② 유사 성향 그룹 포트폴리오 비교 ③ 보유 기업/산업 코멘트",
    "fallback":   "그 외"
}

# Few-shot examples
few_shot_examples = [
    # market
    ("시황정보가 어떻게 돼?",     "market"),
    ("요즘 시황 어때?",       "market"),
    ("전 주의 대표기사 알려줘","market"),
    ("요즘 경제 어때?","market"),
    ("전반적인 시황에 대해서 알려줘","market"),
    ("증시정보 Agent","market"),
    # enterprise
    ("애플 향후 전망이 어떻게 돼?",   "enterprise"),
    ("아마존 요즘 어때?",    "enterprise"),
    ("월마트 기업에 대해서 궁금해",   "enterprise"),
    ("테슬라 기업에 대해 알려줘",   "enterprise"),
    ("기업정보 Agent",   "enterprise"),
    # industry
    ("반도체 시장 분위기 어때?",     "industry"),
    ("AI 산업에 대해서 알려줘",       "industry"),
    ("요즘 인공지능 산업의 전반적인 상황이 어때?", "industry"),
    ("산업정보 Agent", "industry"),
    # personal
    ("xxx 고객이 보유한 종목 알려줘",     "personal"),
    ("xxx 고객 포트폴리오 비교해줘",      "personal"),
    ("xxx 고객 포트폴리오에 대해서 알려줘","personal"),
    ("고객맞춤 Agent","personal"),
]

def classify_intent(text: str) -> str:
    examples = "\n".join(f"{q} → {lbl}" for q, lbl in few_shot_examples)
    prompt = f"""아래 예시를 보고, 새 문장이 어떤 카테고리인지 분류해줘. market / enterprise / industry / personal 중 하나에 해당하지 않으면 fallback 으로 분류해주세요.
{examples}

문장: "{text}"
→ 카테고리:
"""
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    label = resp.choices[0].message.content.strip()
    return label if label in INTENTS else "fallback"

EXTRACTION_PROMPT = """아래 문장을 분석해서 JSON으로 결과만 내려줘.

- intent: market, enterprise, industry, personal, fallback 중 하나
- intent가 \"enterprise\"면:
    • company_name: (예: 엔비디아)
    • symbol: 미국 주식 티커 (예: NVDA)
    • 만약 티커(symbol)만 입력된 경우에도 해당 티커의 기업명을 추출해서 company_name에 넣어줘 (예: \"GS 기업 주가 어때?\" → {{ \"intent\": \"enterprise\", \"company_name\": \"goldman sachs\", \"symbol\": \"GS\" }})
- intent가 \"industry\"면:
    • industry_keyword: (예: 반도체)
    • category: 다음 중 하나 → Technology, Consumer Discretionary, Finance, Health Care, Industrials, Energy, Real Estate, Utilities, Consumer Staples, Telecommunications, Basic Materials, Miscellaneous
- intent가 \"personal\"이면:
    • customer_name: 문장에서 추출한 고객 이름 (예: 김철수)

문장: \"{text}\"
→
"""

def extract_details(text: str) -> dict:
    prompt = EXTRACTION_PROMPT.format(text=text)
    resp = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    content = resp.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"intent": "fallback"}

def generate_fallback_answer(text: str) -> str:
    prompt = f"""아래 질문에 대해 친절하게 답변해줘.

질문: "{text}"
→ 답변:"""
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content.strip()

def classify_and_extract(text: str) -> dict:
    intent = classify_intent(text)
    if intent in ("enterprise", "industry", "personal"):  # personal 추가
        details = extract_details(text)
        if details.get("intent") == intent:
            return details
    if intent == "fallback":
        answer = generate_fallback_answer(text)
        return {"intent": "fallback", "answer": answer}
    return {"intent": intent}

if __name__ == "__main__":
    print("질문을 입력하세요 (종료: 빈 줄 입력)\n")
    while True:
        user_input = input("🖋️  ")
        if not user_input.strip():
            print("종료합니다.")
            break

        result = classify_and_extract(user_input)
        print("→", json.dumps(result, ensure_ascii=False, indent=2), "\n")
