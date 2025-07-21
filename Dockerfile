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

# 임시 파일 정리
RUN rm -f /tmp/download_bart.py /tmp/download_st.py

# 백엔드 코드 복사
COPY app/ ./app/

# 빌드된 프론트엔드 정적 파일 복사
COPY --from=frontend-builder /app/frontend/build ./static

# 환경변수 설정 (PORT는 Cloud Run이 자동으로 설정하므로 제거)
ENV PYTHONPATH=/app

# Cloud Run은 동적으로 포트를 할당하므로 기본값만 설정
ENV PORT=8080

# 포트 노출 (동적으로 변경 가능)
EXPOSE $PORT

# 헬스체크 추가 (PORT 환경변수 사용)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# FastAPI 서버 실행 (PORT 환경변수를 동적으로 사용)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1