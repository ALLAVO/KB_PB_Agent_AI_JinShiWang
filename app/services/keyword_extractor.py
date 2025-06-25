import os
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "120"

import string
from app.db.connection import check_db_connection
from app.services.sentiment import get_weekly_sentiment_scores_by_stock_symbol
from pathlib import Path
from sentence_transformers import SentenceTransformer
import spacy
from keybert import KeyBERT
from transformers import AutoTokenizer

'''
[유의사항]
아래 spaCy 내부에 필요한 추가 리소스는 별도의 다운로드가 필요함
`python -m spacy download en_core_web_sm`
'''

# 모델 및 토크나이저 캐시 경로 지정
paraphrase_model_dir = Path("./tokenizer_cache/paraphrase-mpnet-base-v2")
if not paraphrase_model_dir.exists() or not any(paraphrase_model_dir.glob("**/pytorch_model.bin")):
    # SentenceTransformer 모델 전체를 다운로드 및 저장
    model = SentenceTransformer("sentence-transformers/paraphrase-mpnet-base-v2", cache_folder=str(paraphrase_model_dir))
else:
    model = SentenceTransformer(str(paraphrase_model_dir))
kw_model = KeyBERT(model)

# bart-large-cnn 토크나이저 캐시 경로 지정 및 불러오기
bart_tokenizer_dir = Path("./tokenizer_cache/bart-large-cnn")
if not bart_tokenizer_dir.exists():
    bart_tokenizer_dir.mkdir(parents=True, exist_ok=True)
    bart_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    bart_tokenizer.save_pretrained(str(bart_tokenizer_dir))
else:
    bart_tokenizer = AutoTokenizer.from_pretrained(str(bart_tokenizer_dir))

# 모델 초기화
nlp = spacy.load("en_core_web_sm")

def remove_last_sentences(text, n=3):
    """마지막 n개의 문장을 제거"""
    sentences = [sent.text for sent in nlp(text).sents]
    return ' '.join(sentences[:-n]) if len(sentences) > n else text

def preprocess(text):
    """전처리: 소문자화, 불필요한 문장��호 제거, lemmatization"""
    keep = {'$', '%', "'", '(', ')', '-'}
    remove = ''.join([p for p in string.punctuation if p not in keep])
    text = text.lower().translate(str.maketrans('', '', remove))

    doc = nlp(text)
    return ' '.join([
        token.lemma_ for token in doc
        if token.is_alpha or '-' in token.text
    ])

def extract_named_entities(text):
    """고유명사 원형 및 소문자 버전 추출"""
    doc = nlp(text)
    original, lowered = set(), set()
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG", "GPE", "LOC", "FAC", "PRODUCT"}:
            orig = ent.text.strip()
            original.add(orig)
            lowered.add(orig.lower())
    return original, lowered

def restore_named_entities(keywords, original_ents, lowered_ents):
    """키워드에 포함된 고유명사를 원형으로 복원"""
    restored = []
    for phrase, score in keywords:
        words = phrase.split()
        new_words = [
            next((orig for orig in original_ents if orig.lower() == w.lower()), w)
            if w.lower() in lowered_ents else w
            for w in words
        ]
        restored.append((' '.join(new_words), score))
    return restored

def extract_keywords(text, model, top_n=10, threshold=0.4):
    """KeyBERT 기반 키��드 추출"""
    cleaned = remove_last_sentences(text)
    processed = preprocess(cleaned)

    keywords = model.extract_keywords(
        processed,
        keyphrase_ngram_range=(1, 3),
        stop_words='english',
        top_n=top_n,
        use_mmr=True,
        diversity=0.5,
        nr_candidates=60
    )

    return [(kw, score) for kw, score in keywords if score >= threshold]

def fetch_articles_from_db(stock_symbol, start_date, end_date):
    conn = check_db_connection()
    if conn is None:
        print("[오류] DB 연결 실패")
        return []
    try:
        cur = conn.cursor()
        query = """
            SELECT article, date, weekstart_sunday
            FROM kb_enterprise_dataset
            WHERE stock_symbol = %s AND date >= %s AND date <= %s
            ORDER BY weekstart_sunday, date DESC;
        """
        cur.execute(query, (stock_symbol, start_date, end_date))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print("[오류] DB에서 기사 불러오기 실패:", e)
        if conn:
            conn.close()
        return []

def keyword_extract_from_articles(stock_symbol, start_date, end_date):
    """
    주어진 종목, 시작일, 종료일에 대해 주차별 top3 기사별 키워드 추출 결과를 반환합니다.
    반환값 예시: { week1: [ {...}, {...}, {...} ], week2: [ {...}, ... ] }
    각 기사별로 'keywords' 필드에 키워드 리스트가 포함됩니다.
    """
    sentiment_result = get_weekly_sentiment_scores_by_stock_symbol(stock_symbol, start_date, end_date)
    weekly_top3 = sentiment_result.get("weekly_top3_articles", {})
    if not weekly_top3:
        print("[오류] 해당 조건에 top3 기사가 없습니다.")
        return {}

    weekly_keywords = {}
    for week, top3_articles in weekly_top3.items():
        article_results = []
        for item in top3_articles:
            article, date, weekstart, score, pos_cnt, neg_cnt = item
            original_ents, lowered_ents = extract_named_entities(article)
            keywords = extract_keywords(article, kw_model)
            keywords = restore_named_entities(keywords, original_ents, lowered_ents)
            # 키워드만 리스트로 저장 (score 없이 키워드만 리스트로 저장)
            keyword_list = [kw for kw, _ in keywords]
            article_results.append({
                'article': article,
                'date': date,
                'weekstart': weekstart,
                'score': score,
                'pos_cnt': pos_cnt,
                'neg_cnt': neg_cnt,
                'keywords': keyword_list  # 키워드 리스트만 저장
            })
        weekly_keywords[week] = article_results
    return weekly_keywords

if __name__ == '__main__':
    stock_symbol = "GS"
    start_date = "2023-12-11"
    end_date = "2023-12-14"
    # 예시: 특정 주식 심볼과 날짜 범위로 키워드 추출 실행
    keyword_extract_from_articles(stock_symbol, start_date, end_date)
