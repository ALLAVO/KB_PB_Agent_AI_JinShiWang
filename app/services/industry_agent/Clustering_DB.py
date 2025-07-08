import pandas as pd
import numpy as np
from datetime import timedelta
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
import hdbscan
import collections
from sklearn.metrics.pairwise import euclidean_distances
from app.db.connection import check_db_connection
from app.services.sentiment import get_sentiment_score_for_article
from app.services.keyword_extractor import extract_keywords, extract_named_entities, restore_named_entities, kw_model
from app.services.summarize import summarize_top3_articles

def prev_sunday(input_date_str: str) -> str:
    """
    주어진 날짜(input_date_str)의 이전 주 일요일(weekstart)을 YYYY-MM-DD 문자열로 반환합니다.
    """
    dt = pd.to_datetime(input_date_str)
    days_to_curr_sunday = (dt.weekday() + 1) % 7
    curr_sunday = dt - timedelta(days=days_to_curr_sunday)
    prev_sun = curr_sunday - timedelta(days=7)
    return prev_sun.strftime("%Y-%m-%d")

def get_articles_by_sector(sector: str, weekstart_sunday: str):
    """
    DB에서 특정 산업 섹터와 주차에 해당하는 기사들을 가져옵니다.
    """
    conn = check_db_connection()
    if conn is None:
        return []
    
    try:
        cur = conn.cursor()
        query = """
            SELECT article, date, weekstart_sunday, article_title, stock_symbol
            FROM kb_enterprise_dataset 
            WHERE sector = %s AND weekstart_sunday = %s
            ORDER BY date DESC;
        """
        cur.execute(query, (sector, weekstart_sunday))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching articles for sector {sector}: {e}")
        if conn:
            conn.close()
        return []

def get_industry_top3_articles(sector: str, start_date: str):
    """
    산업군과 시작일을 받아 클러스터링을 통한 상위 3개 대표 기사를 반환합니다.
    """
    prev_sun = prev_sunday(start_date)
    
    # DB에서 해당 섹터의 기사들 가져오기
    articles_data = get_articles_by_sector(sector, prev_sun)
    
    if not articles_data:
        print(f"❗ {sector} 섹터의 {prev_sun} 주차에 기사 데이터가 없습니다.")
        return {"top3_articles": [], "week": prev_sun}
    
    # 기사 제목 추출 및 클리닝
    valid_articles = []
    titles = []
    
    for article, date, weekstart, article_title, stock_symbol in articles_data:
        if article_title and article_title.strip():
            valid_articles.append({
                'article': article,
                'date': date,
                'weekstart': weekstart,
                'article_title': article_title,
                'stock_symbol': stock_symbol
            })
            titles.append(article_title.strip())
    
    if len(titles) < 3:
        print(f"❗ {sector} 섹터의 기사가 충분하지 않습니다. (필요: 3개, 현재: {len(titles)}개)")
        return {"top3_articles": [], "week": prev_sun}
    
    # 1) 임베딩 모델 준비
    embedding_model = SentenceTransformer('all-mpnet-base-v2')
    # ② 바로 여기 아래에 UMAP/HDBSCAN 모델 생성
    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        metric='cosine',
        random_state=42
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=3,
        metric='euclidean',
        cluster_selection_method='eom',
        prediction_data=True
    )

    # 2) BERTopic 모델 생성 및 학습
    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,            # ③ 이 인자
        hdbscan_model=hdbscan_model,      # ③ 이 인자
        calculate_probabilities=False,
        nr_topics='auto'
    )
    topics, probs = topic_model.fit_transform(titles)
    
    # 3) 토픽 정보 확인 및 상위 3개 토픽 추출
    topic_info = topic_model.get_topic_info()
    valid_info = topic_info[topic_info.Topic != -1]
    # -1은 노이즈 토픽이므로 제외
    # 3-1) 상위 3개 토픽 ID
    top_topics = valid_info.head(3).Topic.tolist()
    top3_articles = []
    # 3-2) 대표 문서 뽑기
    for topic_id in top_topics:
        rep_docs = topic_model.get_representative_docs(topic_id)
        if rep_docs:
            rep_title = rep_docs[0]
            idx = titles.index(rep_title)
            top3_articles.append(valid_articles[idx])

    # 3-3) 부족한 경우 노이즈 토픽에서 보강
    if len(top3_articles) < 3:
        # 노이즈 토픽(-1) 문서 제목 리스트
        noise_titles = topic_model.get_representative_docs(-1)
        for title in noise_titles:
            if len(top3_articles) >= 3:
                break
            if title in titles:
                idx = titles.index(title)
                top3_articles.append(valid_articles[idx])

    # 3-4) 그래도 부족하면 전체에서 랜덤 보강
    import random
    while len(top3_articles) < 3:
        idx = random.choice(range(len(valid_articles)))
        if valid_articles[idx] not in top3_articles:
            top3_articles.append(valid_articles[idx])
    
    # 4) 각 기사에 대해 감성점수, 키워드, 요약 추가
    enriched_articles = []
    conn = check_db_connection()
    
    for article_data in top3_articles:
        # 감성점수 계산
        sentiment_score = get_sentiment_score_for_article(article_data['article'], conn)
        
        # 키워드 추출
        original_ents, lowered_ents = extract_named_entities(article_data['article'])
        keywords = extract_keywords(article_data['article'], kw_model)
        keywords = restore_named_entities(keywords, original_ents, lowered_ents)
        keyword_list = [kw for kw, _ in keywords]
        
        enriched_article = {
            'article': article_data['article'],
            'date': article_data['date'].strftime('%Y-%m-%d') if hasattr(article_data['date'], 'strftime') else str(article_data['date']),
            'weekstart': article_data['weekstart'].strftime('%Y-%m-%d') if hasattr(article_data['weekstart'], 'strftime') else str(article_data['weekstart']),
            'article_title': article_data['article_title'],
            'stock_symbol': article_data['stock_symbol'],
            'score': sentiment_score,
            'keywords': keyword_list
        }
        enriched_articles.append(enriched_article)
    
    if conn:
        conn.close()
    
    # 5) 요약 추가 (기존 함수 활용을 위해 형식 맞추기)
    summary_input = []
    for article in enriched_articles:
        summary_input.append({
            'article': article['article'],
            'date': article['date'],
            'weekstart': article['weekstart'],
            'score': article['score'],
            'pos_cnt': 0,  # 임시값
            'neg_cnt': 0,  # 임시값
            'article_title': article['article_title']
        })
    
    summarized_articles = summarize_top3_articles(summary_input)
    
    # 최종 결과 구성
    final_articles = []
    for i, article in enumerate(enriched_articles):
        final_article = article.copy()
        if i < len(summarized_articles):
            final_article['summary'] = summarized_articles[i]['summary']
        else:
            final_article['summary'] = "요약을 생성할 수 없습니다."
        final_articles.append(final_article)
    
    print(f"=== {sector} 섹터 {prev_sun} 주차 상위 3개 클러스터 대표 기사 ===")
    for i, article in enumerate(final_articles, 1):
        print(f"[기사 {i}] 종목: {article['stock_symbol']}, 제목: {article['article_title']}")
        print(f"감성점수: {article['score']}, 키워드: {article['keywords'][:3]}")
    
    return {
        "top3_articles": final_articles,
        "week": prev_sun
    }
