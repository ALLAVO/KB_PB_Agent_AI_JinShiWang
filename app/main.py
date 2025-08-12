# FastAPI 앱 실행 엔트리포인트
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import company, prediction, sentiment, market, summarize, keyword_extractor, stock_chart, return_analysis, industry, clients, portfolio_charts, financial_metrics, valuation, company_sector
from app.api.intention import router as intention
from app.services.cache_manager import load_mcdonald_dictionary

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# CORS 설정: 프론트엔드(React) 개발 서버에서 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://jinshiwang-agent-ai.com",
        "https://www.jinshiwang-agent-ai.com",
        "*"  # 임시로 모든 도메인 허용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router, prefix="/api/v1")
app.include_router(prediction.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")  # sentiment 라우터 prefix 추가
app.include_router(market.router, prefix="/api/v1")  # market 라우터 prefix 추가
app.include_router(summarize.router, prefix="/api/v1")  # summarize 라우터 prefix 추가
app.include_router(keyword_extractor.router, prefix="/api/v1")  # keyword_extractor 라우터 prefix 추가
app.include_router(stock_chart.router, prefix="/api/v1")  # stock_chart 라우터 prefix 추가
app.include_router(return_analysis.router, prefix="/api/v1", tags=["return-analysis"])
app.include_router(intention, prefix="/api/v1", tags=["intention"])  # intention_api 라우터 prefix 추가
app.include_router(industry.router, prefix="/api/v1", tags=["industry"])  # industry 라우터 prefix 수정
app.include_router(clients.router, prefix="/api/v1", tags=["clients"])  # clients 라우터 추가
app.include_router(portfolio_charts.router, prefix="/api/v1", tags=["portfolio-charts"])  # portfolio_charts 라우터 추가
app.include_router(financial_metrics.router, prefix="/api/v1", tags=["financial-metrics"])  # financial_metrics 라우터 추가
app.include_router(valuation.router, prefix="/api/v1", tags=["valuation"])  # valuation 라우터 추가
app.include_router(company_sector.router, prefix="/api/v1", tags=["company-sector"])  # company_sector 라우터 추가

@app.get("/")
def read_root():
    port = os.environ.get("PORT", "8080")
    logger.info(f"Root endpoint accessed, running on port {port}")
    return {
        "Hello": "World", 
        "status": "healthy",
        "port": port,
        "message": "JinShiWang PB Agent AI is running"
    }

@app.get("/health")
def health_check():
    """Cloud Run 헬스체크용 엔드포인트"""
    port = os.environ.get("PORT", "8080")
    logger.info(f"Health check accessed, port: {port}")
    return {
        "status": "healthy", 
        "message": "Service is running",
        "port": port
    }

@app.get("/readiness")
def readiness_check():
    """준비 상태 확인용 엔드포인트"""
    logger.info("Readiness check accessed")
    return {"status": "ready", "message": "Service is ready to serve requests"}

@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 실행되는 이벤트
    """
    port = os.environ.get("PORT", "8080")
    logger.info("🚀 FastAPI 애플리케이션이 시작됩니다.")
    logger.info(f"🌐 포트: {port}")
    logger.info(f"🐍 Python Path: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    try:
        # McDonald 사전을 메모리에 로드
        logger.info("📖 McDonald 사전 로딩 시작...")
        load_mcdonald_dictionary()
        logger.info("✅ McDonald 사전 로드 완료")
    except Exception as e:
        logger.error(f"⚠️ McDonald 사전 로드 중 오류: {e}")
        # 이 오류로 인해 서버가 시작되지 않는 것을 방지
    
    logger.info("✅ 애플리케이션 초기화 완료")
    logger.info(f"📡 서비스가 포트 {port}에서 실행 중입니다.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    애플리케이션 종료 시 실행되는 이벤트
    """
    logger.info("🛑 FastAPI 애플리케이션이 종료됩니다.")

# Cloud Run 환경에서 직접 실행될 경우를 위한 설정
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌟 서버를 포트 {port}에서 시작합니다...")
    logger.info(f"🏠 호스트: 0.0.0.0")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=port,
        reload=False,
        access_log=True,
        log_level="info"
    )