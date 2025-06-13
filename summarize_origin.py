import pandas as pd
from transformers import pipeline, AutoTokenizer
import torch
import psycopg2
from app.core.config import settings
import os
from pathlib import Path


def main():
    # 데이터 로딩 (DB에서 불러오기)
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        # 모든 기업 데이터 불러오기
        query = "SELECT * FROM kb_enterprise_data"
        # 쿼리 결과를 pandas DataFrame으로 변환
        kb_ent_sam = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        print("DB에서 데이터 불러오기 실패:", e)
        return

    # 토크나이저 로드 (BART 기준)
    tokenizer_dir = Path("./tokenizer_cache/bart-large-cnn")
    if not tokenizer_dir.exists():
        tokenizer_dir.mkdir(parents=True, exist_ok=True)
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        tokenizer.save_pretrained(str(tokenizer_dir))
    else:
        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))

    # GPU 사용 여부 확인
    device = 0 if torch.cuda.is_available() else -1
    print(f"사용 중인 디바이스: {'GPU' if device == 0 else 'CPU'}")

    # 토큰 수 계산 함수
    def count_tokens(text):
        if pd.isnull(text) or not isinstance(text, str):
            return 0
        return len(tokenizer.encode(text, truncation=False))

    # 길이 분류 함수
    def classify_length(token_count):
        if token_count <= 200:
            return "short"
        elif token_count <= 700:
            return "medium"
        elif token_count <= 1000:
            return "long"
        else:
            return "very_long"

    # 길이 정보 반환 함수
    def get_length_info(df, idx):
        text = df.loc[idx, "article"]
        tokens = count_tokens(text)
        length_cls = classify_length(tokens)
        return tokens, length_cls

    # Summarizer 파이프라인 로드
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

    # 요약 수행 함수
    def summarize_by_length(df, idx):
        text = df.loc[idx, "article"]
        tokens, cls = get_length_info(df, idx)

        if cls == "short":
            return text

        if cls in ("medium", "long"):
            if cls == "medium":
                max_len = max(50, int(tokens * 0.2))
            else:
                max_len = max(75, int(tokens * 0.15))
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

    # 모델 이름 매핑
    model_names = {
        "short": "(원문 그대로)",
        "medium": "facebook/bart-large-cnn",
        "long": "google/pegasus-cnn_dailymail",
        "very_long": "allenai/led-base-16384"
    }

    # 사용자 입력
    row_index = int(input("요약할 행 인덱스를 입력하세요: "))

    # 정보 취합 및 요약
    tokens, cls = get_length_info(kb_ent_sam, row_index)
    summary = summarize_by_length(kb_ent_sam, row_index)
    model_used = model_names.get(cls, "(알 수 없음)")

    # 결과 출력
    print(f"\n--- 행 {row_index} 요약 정보 ---")
    print(f"토큰 수       : {tokens}")
    print(f"길이 분류     : {cls}")
    print(f"사용 모델     : {model_used}")
    print("\n--- 원문 ---")
    print(kb_ent_sam.loc[row_index, "article"])
    print("\n--- 요약 ---")
    print(summary)

if __name__ == "__main__":
    main()