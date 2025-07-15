##수정본
import pandas as pd
import numpy as np
from datetime import timedelta
from sentence_transformers import SentenceTransformer
import hdbscan
import collections
from sklearn.metrics.pairwise import euclidean_distances


def prev_sunday(input_date_str: str) -> str:
    """
    주어진 날짜(input_date_str)의 이전 주 일요일(weekstart)을 YYYY-MM-DD 문자열로 반환합니다.
    """
    dt = pd.to_datetime(input_date_str)
    days_to_curr_sunday = (dt.weekday() + 1) % 7
    curr_sunday = dt - timedelta(days=days_to_curr_sunday)
    prev_sun = curr_sunday - timedelta(days=7)
    return prev_sun.strftime("%Y-%m-%d")


def main():
    input_date = input("날짜 입력 (예: 2025-06-07): ")
    prev_sun = prev_sunday(input_date)

    df = pd.read_csv('KB_market_data_00.csv') 
    week_df = df[df['weekstart_sunday'] == prev_sun] ## 데이터베이스에서 weekstart_sunday가 prev_sun인 행을 Select 하는 쿼리를 짜고 그 결과를 week_df에 넣으면될듯
    non_na_df = week_df.dropna(subset=['Article_title'])
    titles = non_na_df['Article_title'].tolist()

    if not titles:
        print(f"❗ {prev_sun} 주차에 기사 제목 데이터가 없습니다.")
        return

    # 1) 임베딩
    model = SentenceTransformer('all-mpnet-base-v2') ## 모델로드하는 파일 따로 만들어서 최적화 할 필요있음
    embeddings = model.encode(titles, show_progress_bar=True)

    # 2) 클러스터링
    clusterer = hdbscan.HDBSCAN(min_cluster_size=3)
    labels = clusterer.fit_predict(embeddings)

    # 3) 상위 3개 클러스터
    cnt = collections.Counter(labels[labels >= 0])
    if len(cnt) < 3:
        print("❗ 클러스터 개수가 부족합니다.")
        return
    top_clusters = [cl[0] for cl in cnt.most_common(3)]

    print(f"=== {prev_sun} 주차 상위 3개 클러스터 대표 기사 ===")
    for cluster_id in top_clusters:
        cluster_idxs = np.where(labels == cluster_id)[0]
        cluster_embs = embeddings[cluster_idxs]
        centroid = cluster_embs.mean(axis=0)
        dists = euclidean_distances([centroid], cluster_embs)[0]
        medoid_pos = cluster_idxs[np.argmin(dists)]

        orig_idx = non_na_df.index[medoid_pos]
        article_id = non_na_df.at[orig_idx, 'ID']
        title = non_na_df.at[orig_idx, 'Article_title']
        print(f"[클러스터 {cluster_id}] ID: {article_id}\t제목: {title}")

if __name__ == '__main__':
    main()
    #for update