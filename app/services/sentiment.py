# 뉴스 감성 분석 로직
# 예: from transformers import pipeline

# sentiment_analyzer = pipeline("sentiment-analysis", model="[사용할 모델]") # 예시

def analyze_sentiment(text: str) -> float:
    """
    뉴스 본문을 받아 감성 점수를 반환합니다.
    점수 범위는 -1.0 (부정) 에서 1.0 (긍정) 사이로 가정합니다.
    실제 모델의 출력에 따라 조정이 필요합니다.
    """
    # 여기에 실제 감성 분석 로직을 구현합니다.
    # 예: result = sentiment_analyzer(text)
    # 예: score = result[0]['score'] if result[0]['label'] == 'POSITIVE' else -result[0]['score']
    # 임시 반환값
    if "긍정적" in text:
        return 0.8
    elif "부정적" in text:
        return -0.7
    return 0.1 # 중립 또는 알 수 없음

import psycopg2
from app.core.config import settings


def check_db_connection():
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM kb_enterprise_data LIMIT 1")
        rows = cur.fetchall()
        print('Sample Data from kb_enterprise_data:')
        for row in rows:
            print(row)
        cur.close()
        conn.close()

    except Exception as e:
        print("Error connecting to the database:", e)

if __name__ == "__main__":
    check_db_connection()