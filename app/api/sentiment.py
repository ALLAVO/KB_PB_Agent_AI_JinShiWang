from fastapi import APIRouter, Query
from typing import Optional
from app.services.sentiment import (
    get_weekly_sentiment_scores_by_stock_symbol,
    get_weekly_top3_articles_by_stock_symbol,
)
from app.services.summarize import summarize_article
from app.schemas.sentiment import (
    WeeklySentimentResponse,
    WeeklySentimentWithSummaryResponse,
    WeeklyTop3ArticlesResponse,
)

router = APIRouter()

# 주식 심볼별 주차별 감성점수 반환 API
@router.get(
    "/sentiment/weekly",
    response_model=WeeklySentimentResponse,
    summary="기업의 주차별 감성점수 및 top3 기사와 감성점수 조회",
    description="stock_symbol, start_date, end_date를 받아 해당 기간 내 주차별 감성점수와 top3 기사를 반환합니다. 예시: /sentiment/weekly?stock_symbol=GS&start_date=2023-12-11&end_date=2023-12-14"
)
def get_weekly_sentiment(
        stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
        start_date: Optional[str] = Query(None, description="시작일, 예: '2023-12-11'"),
        end_date: Optional[str] = Query(None, description="종료일, 예: '2023-12-14'")):
    """
    주차별 감성점수 및 top3 기사 반환 API
    """
    result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    if not result or not isinstance(result, dict):
        return WeeklySentimentResponse(weekly_scores={}, weekly_top3_articles={})
    weekly_scores = result.get("weekly_scores", {})
    weekly_top3_articles = {
        week: [
            f"날짜: {art[1]}, 점수: {art[3]}, pos_cnt: {art[4]}, neg_cnt: {art[5]}"
            for art in articles
        ]
        for week, articles in result.get("weekly_top3_articles", {}).items()
    }
    return WeeklySentimentResponse(
        weekly_scores=weekly_scores,
        weekly_top3_articles=weekly_top3_articles
    )

@router.get("/sentiment/weekly_with_summary", response_model=WeeklySentimentWithSummaryResponse)
def weekly_sentiment_with_summary(
        stock_symbol: str = Query(...),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None)):
    """
    주식 심볼별 주차별 감성점수와 기사 요약 반환 API
    """
    sentiment_result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    summary_result = summarize_article(stock_symbol, start_date, end_date)
    return {
        "sentiment": sentiment_result if sentiment_result else {},
        "summaries": summary_result if summary_result else {}
    }

@router.get(
    "/sentiment/weekly_top3_articles",
    response_model=WeeklyTop3ArticlesResponse,
    summary="주차별 top3 기사 원본 반환",
    description="stock_symbol, start_date, end_date를 받아 주차별 top3 기사(기사, 날짜, weekstart, score, pos_cnt, neg_cnt)를 반환합니다.",
    tags=["article analyze"]
)
def get_weekly_top3_articles(
        stock_symbol: str = Query(..., description="종목 코드, 예: 'GS'"),
        start_date: Optional[str] = Query(None, description="시작일, 예: '2023-12-11'"),
        end_date: Optional[str] = Query(None, description="종료일, 예: '2023-12-14'")):
    """
    주차별 top3 기사 원본 반환 API
    """
    result = get_weekly_top3_articles_by_stock_symbol(stock_symbol, start_date, end_date)
    return WeeklyTop3ArticlesResponse(weekly_top3_articles=result)
'''
[response_body 예시: 일부만 표시]
,
      [
        "By Lananh Nguyen NEW YORK, Dec 12 (Reuters) - Goldman Sachs' GS.N head of global commodities Ed Emerson will retire in March after more than 24 years at the Wall Street giant, according to a memo seen by Reuters. He will be succeeded by Xiao Qin and Nitin Jindal, who will jointly lead the firm's storied commodities business, according to a separate memo. Acompany spokesperson confirmed the contents of the memo. Revenue from Goldman's commodities business has been significantly lower in the first three quarters of 2023, according to the company's earnings filings. Still, the business has been a bright spot in results in recent years. Emerson, 47, will become an advisory director to Goldman after he steps down. The executive joined the firm in 1999 as an analyst and climbed the ranks to become managing director in 2008, then partner in 2012. \"He played a critical role in advancing the firm's oil business,\" wrote Ashok Varadhan, Dan Dees and Jim Esposito, the three leaders of Goldman's global banking and markets division, in a memo. Emerson helped \"cement Goldman Sachs' position as a leading franchise in commodities,\" they added. He previously ran global oil and refined products trading. Qin leads commodities trading in Europe, the Middle East, Africa and Asia Pacific. He also runs trading for oil and refined products worldwide. The executive was promoted to managing director in 2010 and partner in 2016. Jindal manages commodities trading in the Americas and natural gas and power trading in North America. He joined Goldman as a partner in 2018. (Reporting by Lananh Nguyen; Editing by Sinead Cruise) ((Lananh.Nguyen@thomsonreuters.com; +1 (646) 696 4829;)) The views and opinions expressed herein are the views and opinions of the author and do not necessarily reflect those of Nasdaq, Inc.",
        "2023-12-12",
        "2023-12-10",
        0.575,
        3,
        0
      ]
    ]
  }
}
'''
