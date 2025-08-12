# Stage 1: 프론트엔드 빌드
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Node.js 의존성 설치
COPY frontend/package*.json ./
RUN npm ci --only=production

# 프론트엔드 소스 코드 복사 및 빌드
COPY frontend/ ./
RUN npm run build

# Stage 2: 백엔드 + 빌드된 프론트엔드
FROM python:3.9-slim

# 시스템 의존성 설치 (psycopg2, 기타 라이브러리용)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# spaCy 영어 모델 설치
RUN python -m spacy download en_core_web_sm

# === 캐시 디렉토리 설정 및 모델 미리 다운로드 ===
# 캐시 디렉토리 환경변수 설정
ENV HF_HOME=/app/tokenizer_cache
ENV TRANSFORMERS_CACHE=/app/tokenizer_cache

# 캐시 디렉토리 생성
RUN mkdir -p /app/tokenizer_cache

# 모델 다운로드 스크립트 생성 및 실행
RUN echo "from transformers import AutoTokenizer; print('Downloading BART...'); AutoTokenizer.from_pretrained('facebook/bart-large-cnn'); print('BART downloaded')" > /tmp/download_bart.py || true
RUN python /tmp/download_bart.py || echo "BART download failed, continuing..."

RUN echo "from sentence_transformers import SentenceTransformer; print('Downloading SentenceTransformer...'); SentenceTransformer('paraphrase-mpnet-base-v2'); print('SentenceTransformer downloaded')" > /tmp/download_st.py || true
RUN python /tmp/download_st.py || echo "SentenceTransformer download failed, continuing..."

RUN rm -f /tmp/download_bart.py /tmp/download_st.py

# 백엔드 코드 복사 (패키지 루트로 app 디렉토리 복사)
COPY app/ ./app

# McDonald 사전 등이 담긴 캐시 디렉토리를 명시적으로 복사
COPY app/cache/ ./app/cache/

# 빌드된 프론트엔드 정적 파일 복사
COPY --from=frontend-builder /app/frontend/build ./static

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

# 애플리케이션 유저 생성 (보안 강화)
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# FastAPI 서버 실행 (Cloud Run PORT 환경변수 사용)
# Shell form 으로 실행해 환경변수 확장 지원
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info"]
