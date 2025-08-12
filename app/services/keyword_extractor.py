import os
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "120"

import string
from app.db.connection import get_sqlalchemy_engine 
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
embedding_model_name = "CatSchroedinger/nomic-v1.5-financial-matryoshka"
financial_model_dir = Path("./tokenizer_cache/nomic-v1.5-financial-matryoshka")
financial_model_dir.mkdir(parents=True, exist_ok=True)

if not financial_model_dir.exists() or not any(financial_model_dir.glob("**/pytorch_model.bin")):
    sentence_model = SentenceTransformer(
        embedding_model_name,
        cache_folder=str(financial_model_dir),
        trust_remote_code=True
    )
else:
    sentence_model = SentenceTransformer(
        str(financial_model_dir),
        trust_remote_code=True
    )

kw_model = KeyBERT(sentence_model)

# # bart-large-cnn 토크나이저 캐시 경로 지정 및 불러오기
# bart_tokenizer_dir = Path("./tokenizer_cache/bart-large-cnn")
# if not bart_tokenizer_dir.exists():
#     bart_tokenizer_dir.mkdir(parents=True, exist_ok=True)
#     bart_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
#     bart_tokenizer.save_pretrained(str(bart_tokenizer_dir))
# else:
#     bart_tokenizer = AutoTokenizer.from_pretrained(str(bart_tokenizer_dir))

# 다운로드 후 저장할 경로
bart_tokenizer_dir = Path("./tokenizer_cache/bart-large-cnn")
bart_tokenizer_dir.parent.mkdir(parents=True, exist_ok=True)  # 상위 폴더 생성

# 디렉토리 초기화 (기존 캐시 삭제 가능 옵션 포함 시 아래 주석 해제)
# import shutil
# if bart_tokenizer_dir.exists():
#     shutil.rmtree(bart_tokenizer_dir)

# Hugging Face에서 항상 새로 다운로드 → 저장
bart_tokenizer = AutoTokenizer.from_pretrained(
    "facebook/bart-large-cnn",
    force_download=True  # 캐시 무시하고 강제 다운로드
)
bart_tokenizer.save_pretrained(str(bart_tokenizer_dir))

# 키워드 추출을 위한 함수 및 spacy 리소스 로딩
nlp = spacy.load("en_core_web_sm")

MAX_TOKENS = 500
CHUNK_OVERLAP = 50

def remove_last_sentences(text, n=3):
    sentences = [sent.text for sent in nlp(text).sents]
    return ' '.join(sentences[:-n]) if len(sentences) > n else text

def extract_named_entities(text):
    doc = nlp(text)
    original, lowered = set(), set()
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG", "GPE", "LOC", "FAC", "PRODUCT"}:
            orig = ent.text.strip()
            original.add(orig)
            lowered.add(orig.lower())
    return original, lowered

def preprocess(text, original_ents):
    keep = {'$', '%', "'", '(', ')', '-'}
    remove = ''.join([p for p in string.punctuation if p not in keep])
    text = text.lower().translate(str.maketrans('', '', remove))
    doc = nlp(text)
    tokens = []
    for token in doc:
        if token.text in original_ents:
            tokens.append(token.text)
        elif token.is_alpha or '-' in token.text:
            tokens.append(token.lemma_)
    return ' '.join(tokens)


def restore_named_entities(keywords, original_ents, lowered_ents):
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
    cleaned = remove_last_sentences(text)
    original_ents, lowered_ents = extract_named_entities(cleaned)
    processed = preprocess(cleaned, original_ents)
    tokens = processed.split()

    if len(tokens) <= MAX_TOKENS:
        keywords = model.extract_keywords(
            processed,
            keyphrase_ngram_range=(1, 3),
            stop_words='english',
            top_n=top_n,
            use_mmr=True,
            diversity=0.5,
            nr_candidates=60
        )
        keywords = restore_named_entities(keywords, original_ents, lowered_ents)
    else:
        keywords_all = []
        chunks = chunk_text(tokens, max_len=MAX_TOKENS, overlap=CHUNK_OVERLAP)
        for chunk_tokens in chunks:
            chunk_text_str = ' '.join(chunk_tokens)
            kws = model.extract_keywords(
                chunk_text_str,
                keyphrase_ngram_range=(1, 3),
                stop_words='english',
                top_n=top_n,
                use_mmr=True,
                diversity=0.5,
                nr_candidates=60
            )
            kws = restore_named_entities(kws, original_ents, lowered_ents)
            keywords_all.extend(kws)
        
        # 점수 평균 or 최대값을 기준으로 병합
        keywords_dict = {}
        for kw, score in keywords_all:
            if kw in keywords_dict:
                keywords_dict[kw].append(score)
            else:
                keywords_dict[kw] = [score]
        
        # 평균 점수 기준 정렬
        keywords = sorted(
            [(kw, sum(scores)/len(scores)) for kw, scores in keywords_dict.items()],
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

    return keywords


def chunk_text(tokens, max_len=400, overlap=50):
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_len, len(tokens))
        chunks.append(tokens[start:end])
        start += max_len - overlap
    return chunks

def fetch_articles_from_db(stock_symbol, start_date, end_date):
    """
    DB에서 기사를 가져옵니다. (SQLAlchemy 엔진 사용)
    """
    engine = get_sqlalchemy_engine()
    try:
        with engine.connect() as conn:
            query = """
                SELECT article, date, weekstart_sunday
                FROM kb_enterprise_dataset
                WHERE stock_symbol = %(stock_symbol)s AND date >= %(start_date)s AND date <= %(end_date)s
                ORDER BY weekstart_sunday, date DESC;
            """
            params = {"stock_symbol": stock_symbol, "start_date": start_date, "end_date": end_date}
            result = conn.execute(query, params)
            rows = result.fetchall()
            return rows
    except Exception as e:
        print("[오류] DB에서 기사 불러오기 실패:", e)
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
            # item은 dict 형태: {'article': ..., 'date': ..., 'weekstart': ..., 'score': ..., 'pos_cnt': ..., 'neg_cnt': ..., 'article_title': ...}
            article = item['article']
            date = item['date']
            weekstart = item['weekstart']
            score = item['score']
            pos_cnt = item['pos_cnt']
            neg_cnt = item['neg_cnt']
            article_title = item.get('article_title', None)
            
            keywords = extract_keywords(article, kw_model)
            article_results.append({
                'article': article,
                'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                'weekstart': weekstart.strftime('%Y-%m-%d') if hasattr(weekstart, 'strftime') else str(weekstart),
                'score': score,
                'pos_cnt': pos_cnt,
                'neg_cnt': neg_cnt,
                'article_title': article_title,
                'keywords': keywords[:5]  # 키워드 리스트만 저장
            })
        weekly_keywords[week] = article_results
    return weekly_keywords

if __name__ == '__main__':
    stock_symbol = "GS"
    start_date = "2023-12-11"
    end_date = "2023-12-14"
    # 예시: 특정 주식 심볼과 날짜 범위로 키워드 추출 실행
    keyword_extract_from_articles(stock_symbol, start_date, end_date)


