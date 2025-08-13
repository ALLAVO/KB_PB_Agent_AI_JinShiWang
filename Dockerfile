# Stage 1: 프론트엔드 빌드
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --frozen-lockfile
COPY frontend/ ./
RUN npm run build

# Stage 2: 백엔드 빌더 (의존성 설치 및 모델 다운로드)
FROM python:3.9-slim AS backend-builder
WORKDIR /app

# 시스템 빌드 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 모델 다운로드 스크립트 복사 및 실행
COPY download_models.py .
RUN python download_models.py

# Stage 3: 최종 실행 이미지 (가장 가볍게)
FROM python:3.9-slim
WORKDIR /app

# 시스템 런타임 의존성만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 빌더에서 설치된 Python 패키지 및 다운로드된 모델 캐시 복사
COPY --from=backend-builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=backend-builder /app/cache /app/cache

# 백엔드 코드 및 프론트엔드 빌드 결과물 복사
COPY app/ ./app
COPY --from=frontend-builder /app/frontend/build ./static

# 환경변수 설정 (매우 중요)
ENV PYTHONPATH=/app
ENV HF_HOME=/app/cache
ENV TRANSFORMERS_CACHE=/app/cache
ENV PORT=8080

EXPOSE 8080

# FastAPI 서버 실행 (workers=1 로 메모리 사용량 안정화)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]