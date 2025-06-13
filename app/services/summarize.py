import pandas as pd
from transformers import pipeline, AutoTokenizer
import torch
import psycopg2
from app.core.config import settings
from pathlib import Path

def summarize_article(stock_symbol: str, start_date: str, end_date: str):
    # 데이터 로딩 (DB에서 불러오기)
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        query = """
            SELECT * FROM kb_enterprise_data
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
            model="google/pegasus-cnn_dailymail",
            device=device
        ),
        "very_long": pipeline(
            "summarization",
            model="allenai/led-base-16384",
            tokenizer="allenai/led-base-16384",
            device=device
        )
    }

    def summarize_by_length(text):
        tokens = count_tokens(text)
        cls = classify_length(tokens)
        if cls == "short":
            return text
        if cls in ("medium", "long"):
            max_len = max(50, int(tokens * 0.2)) if cls == "medium" else max(75, int(tokens * 0.15))
            return summarizers[cls](
                text,
                max_length=max_len,
                min_length=50,
                truncation=True
            )[0]["summary_text"]
        # very_long 처리 (Chunking)
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
        final_summary = summarizers["very_long"](
            combined,
            max_length=200,
            min_length=75,
            truncation=True
        )[0]["summary_text"]
        return final_summary

    results = []
    for idx, row in kb_ent_sam.iterrows():
        article = row["article"]
        summary = summarize_by_length(article)
        results.append({
            "date": row["date"],
            "article": article,
            "summary": summary
        })

    return results

# 예시 실행 및 결과 출력
if __name__ == "__main__":
    stock_symbol = "AAPL"
    start_date = "2022-07-02"
    end_date = "2022-07-03"
    summaries = summarize_article(stock_symbol, start_date, end_date)
    for item in summaries:
        print(f"날짜: {item['date']}")
        print(f"요약: {item['summary']}")
        print("=" * 40)