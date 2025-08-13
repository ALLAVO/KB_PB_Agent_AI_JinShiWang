import os
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import spacy

# 캐시 디렉토리 설정
CACHE_DIR = "./cache"
os.environ['HF_HOME'] = CACHE_DIR
os.environ['TRANSFORMERS_CACHE'] = CACHE_DIR

# 다운로드할 모델 리스트
MODELS_TO_DOWNLOAD = {
    "nomic": "nomic-ai/nomic-bert-2048",
    "bart": "facebook/bart-large-cnn",
    "sentence_transformer": "paraphrase-mpnet-base-v2"
}

def download():
    """필요한 모든 모델을 미리 다운로드합니다."""
    print("모델 다운로드를 시작합니다...")
    os.makedirs(CACHE_DIR, exist_ok=True)

    # 1. Nomic-BERT
    try:
        print(f"Downloading: {MODELS_TO_DOWNLOAD['nomic']}")
        AutoTokenizer.from_pretrained(MODELS_TO_DOWNLOAD['nomic'], trust_remote_code=True, cache_dir=CACHE_DIR)
        AutoModel.from_pretrained(MODELS_TO_DOWNLOAD['nomic'], trust_remote_code=True, cache_dir=CACHE_DIR)
        print(f"'{MODELS_TO_DOWNLOAD['nomic']}' 다운로드 완료.")
    except Exception as e:
        print(f"'{MODELS_TO_DOWNLOAD['nomic']}' 다운로드 실패: {e}")

    # 2. BART
    try:
        print(f"Downloading: {MODELS_TO_DOWNLOAD['bart']}")
        AutoTokenizer.from_pretrained(MODELS_TO_DOWNLOAD['bart'], cache_dir=CACHE_DIR)
        print(f"'{MODELS_TO_DOWNLOAD['bart']}' 다운로드 완료.")
    except Exception as e:
        print(f"'{MODELS_TO_DOWNLOAD['bart']}' 다운로드 실패: {e}")

    # 3. SentenceTransformer
    try:
        print(f"Downloading: {MODELS_TO_DOWNLOAD['sentence_transformer']}")
        SentenceTransformer(MODELS_TO_DOWNLOAD['sentence_transformer'], cache_folder=CACHE_DIR)
        print(f"'{MODELS_TO_DOWNLOAD['sentence_transformer']}' 다운로드 완료.")
    except Exception as e:
        print(f"'{MODELS_TO_DOWNLOAD['sentence_transformer']}' 다운로드 실패: {e}")

    # 4. spaCy 모델
    try:
        print("Downloading: en_core_web_sm")
        spacy.cli.download("en_core_web_sm")
        print("'en_core_web_sm' 다운로드 완료.")
    except Exception as e:
        print(f"'en_core_web_sm' 다운로드 실패: {e}")

    print("모든 모델 다운로드 시도 완료.")

if __name__ == "__main__":
    download()