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

# 캐시 디렉토리 생성 및 모델 다운로드
RUN mkdir -p /app/tokenizer_cache

# 모델 다운로드를 별도로 처리하여 오류 시에도 계속 진행
RUN python -c "try:\n    from transformers import AutoTokenizer\n    AutoTokenizer.from_pretrained('facebook/bart-large-cnn')\n    print('BART tokenizer downloaded successfully')\nexcept Exception as e:\n    print(f'BART tokenizer download failed: {e}')"

RUN python -c "try:\n    from sentence_transformers import SentenceTransformer\n    SentenceTransformer('paraphrase-mpnet-base-v2')\n    print('SentenceTransformer downloaded successfully')\nexcept Exception as e:\n    print(f'SentenceTransformer download failed: {e}')"

# main.py 복사 (루트 레벨에)
COPY app/main.py .

# 백엔드 코드 복사
COPY app/ ./app/

# 빌드된 프론트엔드 정적 파일 복사
COPY --from=frontend-builder /app/frontend/build ./static

# Cloud Run 포트 설정
ENV PORT=8080
ENV PYTHONPATH=/app

# 포트 노출
EXPOSE 8080

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]