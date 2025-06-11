import psycopg2
from app.core.config import settings
from datetime import timedelta
import re

# DB 연결 테스트 및 샘플 데이터 조회
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

def get_articles_by_stock_symbol(stock_symbol: str, start_date: str = None, end_date: str = None):
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        cur = conn.cursor()
        stock_symbol_param = str(stock_symbol).strip()
        # 날짜 조건 동적 생성
        date_conditions = []
        params = [stock_symbol_param]
        if start_date:
            date_conditions.append("date >= %s")
            params.append(start_date)
        if end_date:
            date_conditions.append("date <= %s")
            params.append(end_date)
        date_query = " AND ".join(date_conditions)
        if date_query:
            date_query = " AND " + date_query
        stock_symbol_query = (
            "SELECT article, date, date_trunc('week', date) AS week_start "
            "FROM kb_enterprise_data "
            "WHERE stock_symbol = %s" + date_query + " "
            "ORDER BY date_trunc('week', date), date DESC;"
        )
        print("실행 쿼리:", stock_symbol_query)
        print("파라미터:", params)
        cur.execute(stock_symbol_query, tuple(params))
        rows = cur.fetchall()
        print(f"조회된 row 수: {len(rows)}")
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print("Error fetching articles for ticker:", stock_symbol, e)
        return []

def preprocess_text(text: str) -> list:
    """
    기사 본문에서 단어만 추출(대문자화, 구두점 제거)
    """
    text = text.upper()
    text = re.sub(r'[^A-Z0-9\s]', '', text)  # 영문 대문자, 숫자, 공백만 남김
    words = text.split()
    return words

# 주어진 기사 본문에서 감성 점수를 계산하는 함수
def get_sentiment_score_for_article(article: str, conn) -> float:
    """
    기사 본문(article)에서 단어별로 mcdonald_masterdictionary 테이블을 참조해 감성점수를 정교하게 계산하여 반환합니다.
    - positive_count, negative_count, positive_score_sum, negative_score_sum을 모두 집계
    - 평균 감성 점수 = (positive_score_sum - negative_score_sum) / (positive_count + negative_count)
    """
    cur = conn.cursor()
    words = preprocess_text(article)
    positive_count = 0
    negative_count = 0
    positive_score_sum = 0.0
    negative_score_sum = 0.0
    for word in words:
        cur.execute("SELECT positive, negative FROM mcdonald_masterdictionary WHERE word = %s", (word,))
        result = cur.fetchone()
        if result:
            positive, negative = result
            if positive > 0:
                positive_count += 1
                positive_score_sum += positive
            if negative > 0:
                negative_count += 1
                negative_score_sum += negative
            # print(f"[DEBUG] 단어: '{word}', positive: {positive}, negative: {negative}, pos_sum: {positive_score_sum}, neg_sum: {negative_score_sum}, pos_cnt: {positive_count}, neg_cnt: {negative_count}")
    cur.close()
    total_count = positive_count + negative_count
    if total_count == 0:
        print("[WARNING] 감성 사전에 매칭되는 단어가 없습니다. 기사 감성점수 0 반환.")
        return 0.0
    sentiment_score = (positive_score_sum - negative_score_sum) / total_count
    print(f"[DEBUG] 기사 감성점수: {sentiment_score} (pos_sum: {positive_score_sum}, neg_sum: {negative_score_sum}, pos_cnt: {positive_count}, neg_cnt: {negative_count})")
    return sentiment_score

# 주식 심볼에 대한 주차별 감성 점수 계산 함수
def get_weekly_sentiment_scores_by_stock_symbol(stock_symbol: str, start_date: str = None, end_date: str = None):
    """
    특정 주식 심볼에 대해 입력받은 기간의 모든 기사에 대해 주차별로 감성점수 평균을 반환합니다.
    반환값 예시: { '2024-05-27': 0.12, '2024-06-03': -0.05, ... }
    """
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        articles = get_articles_by_stock_symbol(stock_symbol, start_date, end_date)
        weekly_scores = {}
        weekly_counts = {}
        for article, date, week_start in articles:
            score = get_sentiment_score_for_article(article, conn)
            print(f"기사 날짜: {date}, 주차: {week_start.strftime('%Y-%m-%d')}, 감성점수: {score}")
            week_key = week_start.strftime('%Y-%m-%d')
            if week_key not in weekly_scores:
                weekly_scores[week_key] = 0.0
                weekly_counts[week_key] = 0
            weekly_scores[week_key] += score
            weekly_counts[week_key] += 1
        for week in weekly_scores:
            weekly_scores[week] /= weekly_counts[week]
        print("주차별 평균 감성점수:", weekly_scores)
        conn.close()
        return weekly_scores
    except Exception as e:
        print("Error calculating weekly sentiment scores:", e)
        return {}

if __name__ == "__main__":
    # 테스트 실행: 심볼을 원하는 것으로 변경
    get_weekly_sentiment_scores_by_stock_symbol("AAPL", "2023-01-01", "2023-01-03")
