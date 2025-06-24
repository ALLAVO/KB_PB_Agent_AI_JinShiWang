from app.db.connection import check_db_connection
from datetime import datetime, timedelta
import re


# DB 연결 테스트 및 샘플 데이터 조회
def print_sample_data():
    conn = check_db_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM kb_enterprise_dataset LIMIT 1")
        rows = cur.fetchall()
        print('Sample Data from kb_enterprise_data:')
        for row in rows:
            print(row)
        cur.close()
        conn.close()
    except Exception as e:
        print("Error fetching sample data:", e)
        if conn:
            conn.close()

def get_articles_by_stock_symbol(stock_symbol: str, start_date: str = None, end_date: str = None):
    conn = check_db_connection()
    if conn is None:
        return []
    try:
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
            "SELECT article, date, weekstart_sunday "
            "FROM kb_enterprise_dataset "
            "WHERE stock_symbol = %s" + date_query + " "
            "ORDER BY weekstart_sunday, date DESC;"
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
        if conn:
            conn.close()
        return []

def preprocess_text(text: str) -> list:
    """
    기사 본문에서 단어만 추출(대문자화, 구두점 제거)
    """
    text = text.upper()
    text = re.sub(r'[^A-Z0-9\s]', '', text)  # 영문 대문자, 숫자, 공백만 남김
    words = text.split()
    return words

# 주어진 기사에 대한 감성 점수 계산 함수
def get_sentiment_score_for_article(article: str, conn=None) -> float:
    if conn is None:
        conn = check_db_connection()
        if conn is None:
            return 0.0
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
    orig_start_date = start_date
    orig_end_date = end_date
    if start_date:
        try:
            start_date_dt = datetime.fromisoformat(start_date)
        except Exception:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        start_date_dt += timedelta(days=1)
        start_date = start_date_dt.strftime('%Y-%m-%d')
    if end_date:
        try:
            end_date_dt = datetime.fromisoformat(end_date)
        except Exception:
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_dt += timedelta(days=1)
        end_date = end_date_dt.strftime('%Y-%m-%d')
    print(f"[DEBUG] 전달받은 값 - stock_symbol: {stock_symbol}, start_date: {start_date}, end_date: {end_date} (원본: {orig_start_date}, {orig_end_date})")
    try:
        conn = check_db_connection()
        if conn is None:
            return {}
        articles = get_articles_by_stock_symbol(stock_symbol, start_date, end_date)
        weekly_scores = {}
        weekly_counts = {}
        weekly_articles = {}  # week별 기사 및 점수 정보 저장
        for article, date, week_start in articles:
            # score = 각 기사 별 감성 점수
            score = get_sentiment_score_for_article(article, conn)
            words = preprocess_text(article)
            pos_cnt, neg_cnt, pos_sum, neg_sum = 0, 0, 0.0, 0.0
            for word in words:
                cur = conn.cursor()
                cur.execute("SELECT positive, negative FROM mcdonald_masterdictionary WHERE word = %s", (word,))
                result = cur.fetchone()
                cur.close()
                if result:
                    positive, negative = result
                    if positive > 0:
                        pos_cnt += 1
                        pos_sum += positive
                    if negative > 0:
                        neg_cnt += 1
                        neg_sum += negative
            week_key = week_start.strftime('%Y-%m-%d')
            if week_key not in weekly_scores:
                weekly_scores[week_key] = 0.0
                weekly_counts[week_key] = 0
                weekly_articles[week_key] = []
            weekly_scores[week_key] += score
            weekly_counts[week_key] += 1
            weekly_articles[week_key].append({
                'article': article,
                'date': date,
                'weekstart': week_start,
                'score': score,
                'pos_cnt': pos_cnt,
                'neg_cnt': neg_cnt
            })
        for week in weekly_scores:
            weekly_scores[week] /= weekly_counts[week]
        for week in weekly_scores:
            weekly_scores[week] = int(round(weekly_scores[week]))
        print("주차별 평균 감성점수:", weekly_scores)

        # 각 주차별로 감성점수와 가장 가까운 3개 기사 추출 (DB 쿼리 없이)
        weekly_top3_articles = {}
        for week in weekly_scores:
            top3 = get_top3_articles_closest_to_weekly_score_from_list(
                weekly_articles[week], weekly_scores[week]
            )
            weekly_top3_articles[week] = top3
        print(f"[DEBUG] {stock_symbol}의 주차별 감성점수: {weekly_scores}")
        print(f"[DEBUG] {stock_symbol}의 주차별 top3 기사: {weekly_top3_articles}")
        conn.close()
        return {"weekly_scores": weekly_scores, "weekly_top3_articles": weekly_top3_articles}
    except Exception as e:
        print("Error calculating weekly sentiment scores:", e)
        return {}

def get_top3_articles_closest_to_weekly_score_from_list(articles, weekly_score):
    """
    기사 리스트에서 감성점수와 가장 가까운 3개 기사 반환
    - 감성점수 차이가 가장 적은 순
    - 동점일 경우 positive+negative count가 더 많은 기사 우선
    반환값: [(article, date, weekstart_sunday, article_score, pos_cnt, neg_cnt), ...]
    """
    scored_articles = []
    for item in articles:
        diff = abs(item['score'] - weekly_score)
        scored_articles.append((item['article'], item['date'], item['weekstart'], item['score'], item['pos_cnt'], item['neg_cnt'], diff))
    scored_articles.sort(key=lambda x: (x[6], -(x[4]+x[5])))
    top3 = [x[:6] for x in scored_articles[:3]]
    return top3

# 기존 get_top3_articles_closest_to_weekly_score 함수는 더 이상 사용하지 않음

if __name__ == "__main__":
    # 테스트 실행: 심볼을 원하는 것으로 변경
    # result = get_weekly_sentiment_scores_by_stock_symbol("GS", "2023-12-11", "2023-12-14")
    result = get_weekly_sentiment_scores_by_stock_symbol("AAPL", "2022-07-11", "2022-07-12")
    print("\n[리팩토링 결과 확인]")
    print("주차별 감성점수:", result.get("weekly_scores"))
    print("주차별 top3 기사:")
    for week, articles in result.get("weekly_top3_articles", {}).items():
        print(f"  {week}:")
        for i, art in enumerate(articles, 1):
            print(f"    {i}. 날짜: {art[1]}, 점수: {art[3]}, pos_cnt: {art[4]}, neg_cnt: {art[5]}")
    '''
    [리팩토링 결과 확인]
    주차별 감성점수: {'2022-07-10': -470}
    주차별 top3 기사:
    2022-07-10:
        1. 날짜: 2022-07-12, 점수: -463.2692307692308, pos_cnt: 10, neg_cnt: 16
        2. 날짜: 2022-07-13, 점수: -602.7, pos_cnt: 7, neg_cnt: 13
        3. 날짜: 2022-07-13, 점수: -669.3333333333334, pos_cnt: 3, neg_cnt: 6
    '''