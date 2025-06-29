import pandas as pd
from transformers import pipeline, AutoTokenizer
import torch
from app.db.connection import check_db_connection
from pathlib import Path
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
import openai
from dotenv import load_dotenv
import os

# .env에서 OPENAI_API_KEY 불러오기
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def summarize_article(stock_symbol: str, start_date: str, end_date: str):
    # 데이터 로딩 (DB에서 불러오기)
    try:
        conn = check_db_connection()
        if conn is None:
            print("DB 연결 실패")
            return []
        query = """
            SELECT date, article
            FROM kb_enterprise_dataset
            WHERE stock_symbol = %s AND date >= %s AND date <= %s
            ORDER BY date
        """
        kb_ent_sam = pd.read_sql(query, conn, params=[stock_symbol, start_date, end_date])
        conn.close()
    except Exception as e:
        print("DB에서 데이터 불러오기 실패:", e)
        return []

    tokenizer_dir = Path("./tokenizer_cache/bart-large-cnn")
    if not tokenizer_dir.exists():
        tokenizer_dir.mkdir(parents=True, exist_ok=True)
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        tokenizer.save_pretrained(str(tokenizer_dir))
    else:
        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))

    device = 0 if torch.cuda.is_available() else -1

    def count_tokens(text):
        if pd.isnull(text) or not isinstance(text, str):
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

    summarizers = {
        "medium": pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=device
        ),
        "long": pipeline(
            "summarization",
            model="facebook/bart-large-cnn",  # Pegasus 대신 BART 사용
            device=device
        ),
        "very_long": pipeline(
            "summarization",
            model="facebook/bart-large-cnn",  # LED 대신 BART 사용 (호환성 문제 해결)
            device=device
        )
    }

    def summarize_by_length(text):
        tokens = count_tokens(text)
        cls = classify_length(tokens)
        if cls == "short":
            eng_summary = text
        elif cls in ("medium", "long"):
            max_len = max(50, int(tokens * 0.2)) if cls == "medium" else max(75, int(tokens * 0.15))
            eng_summary = summarizers[cls](
                text,
                max_length=max_len,
                min_length=50,
                truncation=True
            )[0]["summary_text"]
        else:
            token_ids = tokenizer.encode(text, truncation=False)
            chunk_size = 1000
            chunks = [
                tokenizer.decode(token_ids[i:i + chunk_size])
                for i in range(0, len(token_ids), chunk_size)
            ]
            interim_summaries = [
                summarizers["very_long"](
                    chunk,
                    max_length=200,
                    min_length=75,
                    truncation=True
                )[0]["summary_text"]
                for chunk in chunks
            ]
            combined = " ".join(interim_summaries)
            eng_summary = summarizers["very_long"](
                combined,
                max_length=200,
                min_length=75,
                truncation=True
            )[0]["summary_text"]
        kor_result = kor_summary(eng_summary)
        return kor_result

    results = []
    for idx, row in kb_ent_sam.iterrows():
        article = row["article"]
        summary = summarize_by_length(article)
        results.append({
            "date": row["date"],
            "summary": summary
        })

    print("return results", results)

    return results

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
    tokenizer_dir = Path("./tokenizer_cache/bart-large-cnn")
    if not tokenizer_dir.exists():
        tokenizer_dir.mkdir(parents=True, exist_ok=True)
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        tokenizer.save_pretrained(str(tokenizer_dir))
    else:
        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))
    device = 0 if torch.cuda.is_available() else -1
    summarizers = {
        "medium": pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=device
        ),
        "long": pipeline(
            "summarization",
            model="facebook/bart-large-cnn",  # Pegasus 대신 BART 사용
            device=device
        ),
        "very_long": pipeline(
            "summarization",
            model="facebook/bart-large-cnn",  # LED 대신 BART 사용 (호환성 문제 해결)
            device=device
        )
    }
    def count_tokens(text):
        if pd.isnull(text) or not isinstance(text, str):
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
        tokens = count_tokens(text)
        cls = classify_length(tokens)
        if cls == "short":
            eng_summary = text
        elif cls in ("medium", "long"):
            max_len = max(50, int(tokens * 0.2)) if cls == "medium" else max(75, int(tokens * 0.15))
            eng_summary = summarizers[cls](
                text,
                max_length=max_len,
                min_length=50,
                truncation=True
            )[0]["summary_text"]
        else:
            token_ids = tokenizer.encode(text, truncation=False)
            chunk_size = 1000
            chunks = [
                tokenizer.decode(token_ids[i:i + chunk_size])
                for i in range(0, len(token_ids), chunk_size)
            ]
            interim_summaries = [
                summarizers["very_long"](
                    chunk,
                    max_length=200,
                    min_length=75,
                    truncation=True
                )[0]["summary_text"]
                for chunk in chunks
            ]
            combined = " ".join(interim_summaries)
            eng_summary = summarizers["very_long"](
                combined,
                max_length=200,
                min_length=75,
                truncation=True
            )[0]["summary_text"]
        kor_result = kor_summary(eng_summary)
        return kor_result

    results = []
    for item in top3_articles:
        # item은 dict 형태: {'article': ..., 'date': ..., 'weekstart': ..., 'score': ..., 'pos_cnt': ..., 'neg_cnt': ..., 'article_title': ...}
        article = item['article']
        date = item['date']
        weekstart = item['weekstart']
        score = item['score']
        pos_cnt = item['pos_cnt']
        neg_cnt = item['neg_cnt']
        article_title = item.get('article_title', None)
        
        summary = summarize_by_length(article)
        results.append({
            'article': article,
            'date': date,
            'weekstart': weekstart,
            'score': score,
            'pos_cnt': pos_cnt,
            'neg_cnt': neg_cnt,
            'article_title': article_title,
            'summary': summary
        })
    return results

def get_weekly_top3_summaries(stock_symbol: str, start_date: str, end_date: str):
    """
    주어진 종목, 시작일, 종료일에 대해 주차별 top3 기사 요약 리스트를 반환합니다.
    반환값 예시: { week1: [ {...}, {...}, {...} ], week2: [ {...}, ... ] }
    """
    sentiment_result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    weekly_top3 = sentiment_result.get("weekly_top3_articles", {})
    weekly_summaries = {}
    for week, top3_articles in weekly_top3.items():
        summaries = summarize_top3_articles(top3_articles)
        weekly_summaries[week] = summaries
    return weekly_summaries



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
