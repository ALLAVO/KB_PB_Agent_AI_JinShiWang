# FastAPI 앱 실행 엔트리포인트
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import customer, company, prediction, report, sentiment, market, summarize, keyword_extractor, stock_chart, return_analysis

app = FastAPI(
    title="KB PB Agent API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# CORS 설정: 프론트엔드(React) 개발 서버에서 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(customer.router, prefix="/api/v1")
app.include_router(company.router, prefix="/api/v1")
app.include_router(prediction.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")  # sentiment 라우터 prefix 추가
app.include_router(market.router, prefix="/api/v1")  # market 라우터 prefix 추가
app.include_router(summarize.router, prefix="/api/v1")  # summarize 라우터 prefix 추가
app.include_router(keyword_extractor.router, prefix="/api/v1")  # keyword_extractor 라우터 prefix 추가
app.include_router(stock_chart.router, prefix="/api/v1", tags=["stock-chart"])  # stock_chart 라우터 prefix 추가
app.include_router(return_analysis.router, prefix="/api/v1", tags=["return-analysis"])

@app.get("/")
def read_root():
    return {"Hello": "World"}