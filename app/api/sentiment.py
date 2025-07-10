from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.sentiment import (
    get_weekly_sentiment_scores_by_stock_symbol,
    get_articles_by_stock_symbol,
    get_sentiment_score_for_article,
    get_top3_articles_closest_to_weekly_score_from_list,
)
from app.services.summarize import summarize_article
from app.schemas.sentiment import (
    WeeklySentimentResponse,
    WeeklySentimentWithSummaryResponse,
    )
from app.services.sentiment import preprocess_text, check_db_connection


router = APIRouter()


@router.get("/sentiment/top3_articles",
    summary="특정 종목의 전체 기사 중 감성점수 평균에 가장 가까운 top3 기사를 감성점수와 함께 반환",
    description="stock_symbol, start_date, end_date를 받아 전체 기사 중 감성점수 평균에 가장 가까운 top3 기사를 반환합니다.",
    tags=["article analyze"]
)
def get_top3_articles_api(
    stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
    start_date: Optional[str] = Query(None, description="시작일, 예: '2023-12-11'"),
    end_date: Optional[str] = Query(None, description="종료일, 예: '2023-12-14'")
):
    # 주어진 기간에 해당하는 기사를 가져옴
    rows = get_articles_by_stock_symbol(stock_symbol, start_date, end_date)
    articles = []
    # 데이터베이스 연결
    conn = check_db_connection()
    for row in rows:
        article, date, weekstart, article_title = row
        # 기사의 감성 점수 계산
        score = get_sentiment_score_for_article(article, conn)
        # 기사를 전처리하여 단어 목록 생성
        words = preprocess_text(article)
        pos_cnt, neg_cnt = 0, 0
        for word in words:
            cur = conn.cursor()
            cur.execute("SELECT positive, negative FROM mcdonald_masterdictionary WHERE word = %s", (word,))
            result = cur.fetchone()
            cur.close()
            if result:
                positive, negative = result
                if positive > 0:
                    pos_cnt += 1
                if negative > 0:
                    neg_cnt += 1
        articles.append({
            'article': article,
            'date': date,
            'weekstart': weekstart,
            'score': score,
            'pos_cnt': pos_cnt,
            'neg_cnt': neg_cnt,
            'article_title': article_title
        })
    if conn:
        conn.close()
    if not articles:
        return JSONResponse(
            content={"top3_articles": []},
            headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
        )
    # 전체 기사 평균 감성점수
    avg_score = sum(a['score'] for a in articles) / len(articles)
    # 평균 감성점수에 가장 가까운 top3 기사 추출
    top3 = get_top3_articles_closest_to_weekly_score_from_list(articles, avg_score)
    return JSONResponse(
        content={"top3_articles": top3},
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    )


