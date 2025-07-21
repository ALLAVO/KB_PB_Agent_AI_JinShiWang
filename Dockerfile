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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 의존성 설치 
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 코드 복사
COPY app/ ./app/

# tokenizer_cache 폴더를 Docker 이미지에 복사 (로컬 구조와 동일하게)
COPY tokenizer_cache/ ./tokenizer_cache/

# 빌드된 프론트엔드 정적 파일 복사
COPY --from=frontend-builder /app/frontend/build ./static
# 또는 프론트엔드가 dist 폴더에 빌드된다면:
# COPY --from=frontend-builder /app/frontend/dist ./static

# === tokenizer_cache 미리 다운로드 (bart-large-cnn, paraphrase-mpnet-base-v2) ===
RUN mkdir -p /app/tokenizer_cache && \
    python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('facebook/bart-large-cnn', cache_dir='/app/tokenizer_cache')" && \
    python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-mpnet-base-v2', cache_folder='/app/tokenizer_cache')\"

# Cloud Run 포트 설정
ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE 8080

# FastAPI 서버 실행 (app 폴더 안의 main.py 실행)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]