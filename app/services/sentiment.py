from app.db.connection import check_db_connection
from app.services.cache_manager import get_mcdonald_word_info
import re

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
            "SELECT article, date, weekstart_sunday, article_title "
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
    words = preprocess_text(article)
    positive_count = 0
    negative_count = 0
    uncertainty_count = 0
    litigious_count = 0
    constraining_count = 0
    
    for word in words:
        word_info = get_mcdonald_word_info(word)
        if word_info:
            if word_info['positive'] > 0:
                positive_count += 1
            if word_info['negative'] > 0:
                negative_count += 1
            if word_info['uncertainty'] > 0:
                uncertainty_count += 1
            if word_info['litigious'] > 0:
                litigious_count += 1
            if word_info['constraining'] > 0:
                constraining_count += 1
    
    total_count = positive_count + negative_count + uncertainty_count + litigious_count + constraining_count
    if total_count == 0:
        print("[WARNING] 감성 사전에 매칭되는 단어가 없습니다. 기사 감성점수 0 반환.")
        return 0.0
    
    # 가중치 적용 (예시)
    alpha = 0.7
    beta = 0.7
    gamma = 0.5
    sentiment_score = (
        positive_count - negative_count
        - alpha * uncertainty_count
        - beta * litigious_count
        - gamma * constraining_count
    ) / total_count
    sentiment_score = round(sentiment_score, 3)
    print(f"[DEBUG] 기사 감성점수: {sentiment_score} (pos_cnt: {positive_count}, neg_cnt: {negative_count}, uncertainty_cnt: {uncertainty_count}, litigious_cnt: {litigious_count}, constraining_cnt: {constraining_count})")
    return sentiment_score

def get_top3_articles_closest_to_weekly_score_from_list(articles, weekly_score):
    """
    기사 리스트에서 감성점수와 가장 가까운 3개 기사 반환
    - 감성점수 차이가 가장 적은 순
    - 동점일 경우 positive+negative count가 더 많은 기사 우선
    반환값: [dict, ...] (각 dict: article, date, weekstart, score, pos_cnt, neg_cnt, article_title)
    {
        'article': ...,
        'date': ...,
        'weekstart': ...,
        'score': ...,
        'pos_cnt': ...,
        'neg_cnt': ...,
        'article_title': ...
    }   
    """
    scored_articles = []
    for item in articles:
        diff = abs(item['score'] - weekly_score)
        scored_articles.append({
            'article': item['article'],
            'date': item['date'],
            'weekstart': item['weekstart'],
            'score': item['score'],
            'pos_cnt': item['pos_cnt'],
            'neg_cnt': item['neg_cnt'],
            'article_title': item.get('article_title', None),
            'diff': diff
        })
    scored_articles.sort(key=lambda x: (x['diff'], -(x['pos_cnt']+x['neg_cnt'])))
    top3 = [
        {
            'article': x['article'],
            'date': x['date'].strftime('%Y-%m-%d') if hasattr(x['date'], 'strftime') else str(x['date']),
            'weekstart': x['weekstart'].strftime('%Y-%m-%d') if hasattr(x['weekstart'], 'strftime') else str(x['weekstart']),
            'score': x['score'],
            'pos_cnt': x['pos_cnt'],
            'neg_cnt': x['neg_cnt'],
            'article_title': x['article_title']
        }
        for x in scored_articles[:3]
    ]
    return top3

# 주식 심볼에 대한 주차별 감성 점수 계산 함수
def get_weekly_sentiment_scores_by_stock_symbol(stock_symbol: str, start_date: str = None, end_date: str = None):
    # start_date, end_date를 하루씩 추가하지 않고 그대로 사용
    orig_start_date = start_date
    orig_end_date = end_date
    print(f"[DEBUG] 전달받은 값 - stock_symbol: {stock_symbol}, start_date: {start_date}, end_date: {end_date} (원본: {orig_start_date}, {orig_end_date})")
    try:
        conn = check_db_connection()
        if conn is None:
            return {}
        articles = get_articles_by_stock_symbol(stock_symbol, start_date, end_date)
        weekly_scores = {}
        weekly_counts = {}
        weekly_articles = {}  # week별 기사 및 점수 정보 저장
        for article, date, week_start, article_title in articles:
            # score = 각 기사 별 감성 점수
            score = get_sentiment_score_for_article(article, conn)
            words = preprocess_text(article)
            pos_cnt, neg_cnt, pos_sum, neg_sum = 0, 0, 0.0, 0.0
            
            for word in words:
                word_info = get_mcdonald_word_info(word)
                if word_info:
                    if word_info['positive'] > 0:
                        pos_cnt += 1
                        pos_sum += word_info['positive']
                    if word_info['negative'] > 0:
                        neg_cnt += 1
                        neg_sum += word_info['negative']
            
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
                'neg_cnt': neg_cnt,
                'article_title': article_title
            })
        for week in weekly_scores:
            weekly_scores[week] /= weekly_counts[week]
            weekly_scores[week] = round(weekly_scores[week], 3)
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


def get_weekly_top3_sentiment_scores(stock_symbol: str, start_date: str = None, end_date: str = None):
    """
    주차별 top3 기사 각각의 감성점수만 반환하는 함수
    Returns:
        dict: {주차: [기사1 점수, 기사2 점수, 기사3 점수], ...}
    """
    result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    weekly_top3_articles = result.get("weekly_top3_articles", {})
    weekly_top3_scores = {}
    for week, articles in weekly_top3_articles.items():
        # articles: list of dicts with keys: article, date, weekstart, score, pos_cnt, neg_cnt, article_title
        weekly_top3_scores[week] = [art['score'] for art in articles]
    return weekly_top3_scores

def get_weekly_top3_articles_by_stock_symbol(stock_symbol: str, start_date: str = None, end_date: str = None):
    """
    주차별 top3 기사를 각 기사의 감성점수와 함꼐 반환하는 함수
    Returns:
        dict: {주차: [dict, ...], ...} (각 dict: article, date, weekstart, score, pos_cnt, neg_cnt, article_title)
    """
    result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    return result.get("weekly_top3_articles", {})


if __name__ == "__main__":
    # 테스트 실행: 심볼을 원하는 것으로 변경
    result = get_weekly_sentiment_scores_by_stock_symbol("GS", "2023-12-11", "2023-12-14")
    # result = get_weekly_sentiment_scores_by_stock_symbol("AAPL", "2022-07-11", "2022-07-12")
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