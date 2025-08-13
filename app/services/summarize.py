import pandas as pd
from transformers import pipeline, AutoTokenizer
import torch
from app.db.connection import get_sqlalchemy_engine
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol, get_weekly_top3_articles_by_stock_symbol
from dotenv import load_dotenv
import openai
import os
from summa.summarizer import summarize as extractive_summarize
from sqlalchemy import text 

CACHE_DIR = os.getenv("HF_HOME")

# .env에서 OPENAI_API_KEY 불러오기
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    model_name = "facebook/bart-large-cnn"
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=CACHE_DIR
    )
    
    device = 0 if torch.cuda.is_available() else -1
    summarizer = pipeline(
        "summarization",
        model=model_name,
        tokenizer=tokenizer, 
        device=device
    )
except Exception as e:
    print(f"Summarization 모델 또는 토크나이저 로딩 중 오류 발생: {e}")
    tokenizer = None
    summarizer = None
    raise

ratio_map = {
    "medium": 0.7,
    "long":   0.6,
    "very_long": 0.5
}

def kor_summary(text: str) -> str:
    """
    영어 텍스트(뉴스 요약문)를 받아 한국어로 번역하고 문장을 자연스럽게 다듬어 반환합니다.
    Args:
        text (str): 번역할 영어 뉴스 요약문.
    Returns:
        str: 한국어로 번역되고 다듬어진 텍스트.
    """
    system_msg = (
        "You are a professional translator and editor specializing in journalism and formal report writing. "
        "The provided English text is a summary of a news article. "
        "Translate it into fluent, formal Korean suitable for inclusion in a business report."
    )
    user_msg = (
        f"Translate and polish the following English news summary into formal Korean, "
        "and present each key point as a bulleted list. "
        "Use polite declarative endings (예: '…입니다', '…예정입니다').\n\n"
        f"{text}"
    )
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=1024,
    )
    kor_final_summary = response.choices[0].message.content.strip()
    return kor_final_summary


def summarize_top3_articles(top3_articles):
    """
    top3_articles: [(article, date, weekstart_sunday, article_score, pos_cnt, neg_cnt), ...]
    각 기사에 대해 요약을 추가하여 반환
    반환값: [
        {
            'article': article,
            'date': date,
            'weekstart': weekstart,
            'score': article_score,
            'pos_cnt': pos_cnt,
            'neg_cnt': neg_cnt,
            'summary': summary
        }, ...
    ]
    """
    
    def count_tokens(text):
        if pd.isnull(text) or not isinstance(text, str) or not tokenizer:
            return 0
        return len(tokenizer.encode(text, truncation=False))

    def classify_length(token_count):
        if token_count <= 200:
            return "short"
        elif token_count <= 700:
            return "medium"
        elif token_count <= 1000:
            return "long"
        else:
            return "very_long"

    def summarize_by_length(text):
        if not summarizer:
            return "요약 모델을 로드할 수 없어 요약을 생성할 수 없습니다."

        tokens = count_tokens(text)
        cls    = classify_length(tokens)

        if cls == "short":
            eng_summary = text
        else:
            ratio = ratio_map[cls]
            extract_text = extractive_summarize(text, ratio=ratio)

            if cls in ("medium", "long"):
                max_len = max(50, int(tokens * 0.2)) if cls == "medium" else max(75, int(tokens * 0.15))
                eng_summary = summarizer(
                    extract_text,
                    max_length=max_len,
                    min_length=50,
                    truncation=True
                )[0]["summary_text"]
            else:  # very_long
                token_ids = tokenizer.encode(extract_text, truncation=False)
                chunk_size = 1000
                chunks = [
                    tokenizer.decode(token_ids[i:i+chunk_size])
                    for i in range(0, len(token_ids), chunk_size)
                ]
                interim = [
                    summarizer(
                        chunk,
                        max_length=200,
                        min_length=75,
                        truncation=True
                    )[0]["summary_text"]
                    for chunk in chunks
                ]
                combined = " ".join(interim)
                eng_summary = summarizer(
                    combined,
                    max_length=200,
                    min_length=75,
                    truncation=True
                )[0]["summary_text"]
        
        return kor_summary(eng_summary)

    results = []
    for item in top3_articles:
        article = item['article']
        
        summary = summarize_by_length(article)
        
        new_item = item.copy()
        new_item['summary'] = summary
        results.append(new_item)
        
    return results

def get_weekly_top3_summaries(stock_symbol: str, start_date: str, end_date: str):
    """
    주어진 기간 동안의 주차별 상위 3개 기사와 요약을 반환합니다.
    """
    weekly_top3_articles = get_weekly_top3_articles_by_stock_symbol(stock_symbol, start_date, end_date)
    
    summarized_weekly_articles = {}
    for week, articles in weekly_top3_articles.items():
        summarized_articles = summarize_top3_articles(articles)
        summarized_weekly_articles[week] = summarized_articles
        
    return summarized_weekly_articles



# 사용 예시 (sentiment.py에서 top3 기사 리스트를 받아 요약)
if __name__ == "__main__":
    # 예시: sentiment.py에서 top3 기사 리스트를 받아옴 (직접 호출 예시)
    stock_symbol = "GS"
    start_date = "2023-12-11"
    end_date = "2023-12-14"
    sentiment_result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    weekly_top3 = sentiment_result.get("weekly_top3_articles", {})
    for week, top3_articles in weekly_top3.items():
        print(f"\n[주차: {week}] Top3 기사 요약 결과:")
        summaries = summarize_top3_articles(top3_articles)
        for i, item in enumerate(summaries, 1):
            print(f"{i}. 날짜: {item['date']}, 점수: {item['score']}, pos_cnt: {item['pos_cnt']}, neg_cnt: {item['neg_cnt']}")
            print(f"요약: {item['summary']}")
            print("-" * 40)
