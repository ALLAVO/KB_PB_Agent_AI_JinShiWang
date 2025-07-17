import pandas as pd
import numpy as np
from datetime import timedelta
from sentence_transformers import SentenceTransformer
import hdbscan
import collections
from sklearn.metrics.pairwise import euclidean_distances
from app.db.connection import check_db_connection
from app.services.sentiment import get_sentiment_score_for_article
from app.services.keyword_extractor import extract_keywords, extract_named_entities, restore_named_entities, kw_model
from app.services.summarize import summarize_top3_articles

def week_start_sunday(input_date_str: str) -> str:
    """
    주어진 날짜(input_date_str)가 포함된 주의 일요일(weekstart)을 YYYY-MM-DD 문자열로 반환합니다.
    """
    dt = pd.to_datetime(input_date_str)
    days_to_curr_sunday = (dt.weekday() + 1) % 7
    curr_sunday = dt - timedelta(days=days_to_curr_sunday)
    return curr_sunday.strftime("%Y-%m-%d")

## 산업 Agent
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

def get_industry_top3_articles(sector: str, end_date: str):
    """
    산업군과 종료일을 받아 클러스터링을 통한 상위 3개 대표 기사를 반환합니다.
    """
    week_sunday = week_start_sunday(end_date)
    
    # DB에서 해당 섹터의 기사들 가져오기
    articles_data = get_articles_by_sector(sector, week_sunday)
    
    if not articles_data:
        print(f"❗ {sector} 섹터의 {week_sunday} 주차에 기사 데이터가 없습니다.")
        return {"top3_articles": [], "week": week_sunday}
    
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
        return {"top3_articles": [], "week": week_sunday}
    
    # 1) 임베딩
    model = SentenceTransformer('all-mpnet-base-v2')
    embeddings = model.encode(titles, show_progress_bar=True)
    
    # 2) 클러스터링
    clusterer = hdbscan.HDBSCAN(min_cluster_size=3)
    labels = clusterer.fit_predict(embeddings)
    
    # 3) 상위 3개 클러스터 찾기
    cnt = collections.Counter(labels[labels >= 0])
    if len(cnt) < 3:
        print(f"❗ 클러스터 개수가 부족합니다. (필요: 3개, 현재: {len(cnt)}개)")
        print(f"📊 총 기사 수: {len(valid_articles)}, 클러스터링된 기사 수: {len(labels[labels >= 0])}, 노이즈 기사 수: {len(labels[labels == -1])}")
        
        # 클러스터가 부족한 경우 가장 큰 클러스터들과 노이즈에서 선택
        available_clusters = [cl[0] for cl in cnt.most_common()]
        noise_indices = np.where(labels == -1)[0]
        
        top3_articles = []
        
        # 기존 클러스터에서 대표 기사 선택
        for cluster_id in available_clusters:
            cluster_idxs = np.where(labels == cluster_id)[0]
            cluster_embs = embeddings[cluster_idxs]
            centroid = cluster_embs.mean(axis=0)
            dists = euclidean_distances([centroid], cluster_embs)[0]
            medoid_pos = cluster_idxs[np.argmin(dists)]
            
            article_data = valid_articles[medoid_pos]
            top3_articles.append(article_data)
        
        print(f"🔍 클러스터에서 선택된 기사 수: {len(top3_articles)}")
        
        # 부족한 만큼 노이즈에서 추가 선택 (무작위)
        needed = 3 - len(top3_articles)
        if needed > 0 and len(noise_indices) > 0:
            print(f"🎲 노이즈에서 {needed}개 기사 추가 선택 (사용 가능한 노이즈: {len(noise_indices)}개)")
            selected_noise = np.random.choice(noise_indices, min(needed, len(noise_indices)), replace=False)
            for idx in selected_noise:
                article_data = valid_articles[idx]
                top3_articles.append(article_data)
        
        # 여전히 부족하면 전체에서 무작위 선택
        remaining_needed = 3 - len(top3_articles)
        if remaining_needed > 0:
            print(f"⚠️ 여전히 {remaining_needed}개 기사 부족 - 전체에서 무작위 선택")
            while len(top3_articles) < 3 and len(valid_articles) > len(top3_articles):
                remaining_indices = [i for i in range(len(valid_articles)) 
                                   if valid_articles[i] not in top3_articles]
                if remaining_indices:
                    selected_idx = np.random.choice(remaining_indices)
                    top3_articles.append(valid_articles[selected_idx])
                else:
                    print("❌ 더 이상 선택할 기사가 없습니다.")
                    break
        
        print(f"✅ 최종 선택된 기사 수: {len(top3_articles)}")
    else:
        top_clusters = [cl[0] for cl in cnt.most_common(3)]
        top3_articles = []
        
        for cluster_id in top_clusters:
            cluster_idxs = np.where(labels == cluster_id)[0]
            cluster_embs = embeddings[cluster_idxs]
            centroid = cluster_embs.mean(axis=0)
            dists = euclidean_distances([centroid], cluster_embs)[0]
            medoid_pos = cluster_idxs[np.argmin(dists)]
            
            article_data = valid_articles[medoid_pos]
            top3_articles.append(article_data)
    
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
    
    print(f"=== {sector} 섹터 {week_sunday} 주차 상위 3개 클러스터 대표 기사 ===")
    for i, article in enumerate(final_articles, 1):
        print(f"[기사 {i}] 종목: {article['stock_symbol']}, 제목: {article['article_title']}")
        print(f"감성점수: {article['score']}, 키워드: {article['keywords'][:3]}")
    
    return {
        "top3_articles": final_articles,
        "week": week_sunday
    }

## 증시 Agent
def get_hot_articles_by_date(start_date: str):
    """
    DB에서 특정 주차에 해당하는 모든 기사들을 가져옵니다. (섹터 구분 없음)
    """
    conn = check_db_connection()
    if conn is None:
        return []
    
    try:
        cur = conn.cursor()
        query = """
            SELECT article, date, weekstart_sunday, article_title, stock_symbol, sector
            FROM kb_enterprise_dataset 
            WHERE weekstart_sunday = %s
            ORDER BY date DESC;
        """
        cur.execute(query, (start_date,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching hot articles for date {start_date}: {e}")
        if conn:
            conn.close()
        return []

def get_market_hot_articles(end_date: str):
    week_sunday = week_start_sunday(end_date)
    articles_data = get_hot_articles_by_date(week_sunday)
    if not articles_data:
        print(f"❗ {week_sunday} 주차에 기사 데이터가 없습니다.")
        return {"top3_articles": [], "week": week_sunday}

    # 기사 제목 추출 및 클리닝
    valid_articles = []
    titles = []
    for article, date, weekstart, article_title, stock_symbol, sector in articles_data:
        if article_title and article_title.strip():
            valid_articles.append({
                'article': article,
                'date': date,
                'weekstart': weekstart,
                'article_title': article_title,
                'stock_symbol': stock_symbol,
                'sector': sector
            })
            titles.append(article_title.strip())
    if len(titles) < 3:
        print(f"❗ {week_sunday} 주차의 기사가 충분하지 않습니다. (필요: 3개, 현재: {len(titles)}개)")
        return {"top3_articles": [], "week": week_sunday}

    # 1) 임베딩 (한 번만)
    model = SentenceTransformer('all-mpnet-base-v2')
    embeddings = model.encode(titles, show_progress_bar=True)

    # 2) 클러스터링 (한 번만)
    clusterer = hdbscan.HDBSCAN(min_cluster_size=3)
    labels = clusterer.fit_predict(embeddings)

    # 3) 상위 3개 클러스터 찾기 (한 번만)
    cnt = collections.Counter(labels[labels >= 0])
    top3_articles = []
    if len(cnt) < 3:
        print(f"❗ 클러스터 개수가 부족합니다. (필요: 3개, 현재: {len(cnt)}개)")
        print(f"📊 총 기사 수: {len(valid_articles)}, 클러스터링된 기사 수: {len(labels[labels >= 0])}, 노이즈 기사 수: {len(labels[labels == -1])}")
        
        # 클러스터가 부족한 경우 가장 큰 클러스터들과 노이즈에서 선택
        available_clusters = [cl[0] for cl in cnt.most_common()]
        noise_indices = np.where(labels == -1)[0]
        # 클러스터 대표 기사 선택
        for cluster_id in available_clusters:
            cluster_idxs = np.where(labels == cluster_id)[0]
            cluster_embs = embeddings[cluster_idxs]
            centroid = cluster_embs.mean(axis=0)
            dists = euclidean_distances([centroid], cluster_embs)[0]
            medoid_pos = cluster_idxs[np.argmin(dists)]
            article_data = valid_articles[medoid_pos]
            top3_articles.append(article_data)
        
        print(f"🔍 클러스터에서 선택된 기사 수: {len(top3_articles)}")
        
        # 부족한 만큼 노이즈에서 추가 선택 (무작위)
        needed = 3 - len(top3_articles)
        if needed > 0 and len(noise_indices) > 0:
            print(f"🎲 노이즈에서 {needed}개 기사 추가 선택 (사용 가능한 노이즈: {len(noise_indices)}개)")
            selected_noise = np.random.choice(noise_indices, min(needed, len(noise_indices)), replace=False)
            for idx in selected_noise:
                article_data = valid_articles[idx]
                top3_articles.append(article_data)
        # 여전히 부족하면 전체에서 무작위 선택
        remaining_needed = 3 - len(top3_articles)
        if remaining_needed > 0:
            print(f"⚠️ 여전히 {remaining_needed}개 기사 부족 - 전체에서 무작위 선택")
            while len(top3_articles) < 3 and len(valid_articles) > len(top3_articles):
                remaining_indices = [i for i in range(len(valid_articles)) if valid_articles[i] not in top3_articles]
                if remaining_indices:
                    selected_idx = np.random.choice(remaining_indices)
                    top3_articles.append(valid_articles[selected_idx])
                else:
                    break
        
        print(f"✅ 최종 선택된 기사 수: {len(top3_articles)}")
    else:
        top_clusters = [cl[0] for cl in cnt.most_common(3)]
        for cluster_id in top_clusters:
            cluster_idxs = np.where(labels == cluster_id)[0]
            cluster_embs = embeddings[cluster_idxs]
            centroid = cluster_embs.mean(axis=0)
            dists = euclidean_distances([centroid], cluster_embs)[0]
            medoid_pos = cluster_idxs[np.argmin(dists)]
            article_data = valid_articles[medoid_pos]
            top3_articles.append(article_data)

    # 4) 각 기사에 대해 감성점수, 키워드, 요약 추가 (한 번만)
    conn = check_db_connection()
    enriched_articles = []
    for article_data in top3_articles:
        # 감성점수, 키워드 추출 한 번만
        sentiment_score = get_sentiment_score_for_article(article_data['article'], conn)
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
            'sector': article_data['sector'],
            'score': sentiment_score,
            'keywords': keyword_list
        }
        enriched_articles.append(enriched_article)
    if conn:
        conn.close()

    # 5) 요약 생성 (한 번만)
    summary_input = [{
        'article': article['article'],
        'date': article['date'],
        'weekstart': article['weekstart'],
        'score': article['score'],
        'pos_cnt': 0,
        'neg_cnt': 0,
        'article_title': article['article_title']
    } for article in enriched_articles]
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

    print(f"=== {week_sunday} 주차 시장 핫한 기사 TOP 3 ===")
    for i, article in enumerate(final_articles, 1):
        print(f"[기사 {i}] 섹터: {article['sector']}, 종목: {article['stock_symbol']}, 제목: {article['article_title']}")
        print(f"감성점수: {article['score']}, 키워드: {article['keywords'][:3]}")

    return {
        "top3_articles": final_articles,
        "week": week_sunday
    }
    
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
    
    print(f"=== {week_sunday} 주차 시장 핫한 기사 TOP 3 ===")
    for i, article in enumerate(final_articles, 1):
        print(f"[기사 {i}] 섹터: {article['sector']}, 종목: {article['stock_symbol']}, 제목: {article['article_title']}")
        print(f"감성점수: {article['score']}, 키워드: {article['keywords'][:3]}")
    
    return {
        "top3_articles": final_articles,
        "week": week_sunday
    }
