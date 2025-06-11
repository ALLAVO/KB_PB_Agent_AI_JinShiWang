from keybert import KeyBERT
import pandas as pd
import string
import spacy

# 모델 초기화
nlp = spacy.load("en_core_web_sm")
kw_model = KeyBERT('sentence-transformers/paraphrase-mpnet-base-v2')

def remove_last_sentences(text, n=3):
    """마지막 n개의 문장을 제거"""
    sentences = [sent.text for sent in nlp(text).sents]
    return ' '.join(sentences[:-n]) if len(sentences) > n else text

def preprocess(text):
    """전처리: 소문자화, 불필요한 문장부호 제거, lemmatization"""
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
    """KeyBERT 기반 키워드 추출"""
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

def main():
    try:
        df = pd.read_csv("test00.csv")
    except FileNotFoundError:
        print("[오류] 'test00.csv' 파일을 찾을 수 없습니다.")
        return

    if 'Article' not in df.columns:
        print("[오류] 'Article' 열이 존재하지 않습니다.")
        return

    idx_input = input("인덱스를 입력하세요: ").strip()
    if not idx_input.isdigit():
        print("[오류] 숫자를 입력해야 합니다.")
        return

    idx = int(idx_input)
    if idx < 0 or idx >= len(df):
        print(f"[오류] 유효한 인덱스 범위는 0 ~ {len(df) - 1} 입니다.")
        return

    text = df.loc[idx, 'Article']

    original_ents, lowered_ents = extract_named_entities(text)
    keywords = extract_keywords(text, kw_model)
    keywords = restore_named_entities(keywords, original_ents, lowered_ents)

    print("\n--- 키워드 추출 결과 ---")
    if keywords:
        for kw, score in keywords:
            print(f"- {kw} (유사도: {score:.4f})")
    else:
        print("유사도 기준 이상의 키워드가 없습니다.")

    print("\n--- 본문 ---")
    print(text)

if __name__ == '__main__':
    main()

