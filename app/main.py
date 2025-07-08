# FastAPI 앱 실행 엔트리포인트
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import company_info, customer, prediction, report, sentiment, market, summarize, keyword_extractor, stock_chart, return_analysis, industry, clients, portfolio_charts
from app.api.intention import router as intention
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
        "http://localhost:3001" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customer.router, prefix="/api/v1")
app.include_router(company_info.router, prefix="/api/v1", tags=["company"])  # company 라우터 추가
app.include_router(prediction.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")  # sentiment 라우터 prefix 추가
app.include_router(market.router, prefix="/api/v1")  # market 라우터 prefix 추가
app.include_router(summarize.router, prefix="/api/v1")  # summarize 라우터 prefix 추가
app.include_router(keyword_extractor.router, prefix="/api/v1")  # keyword_extractor 라우터 prefix 추가
app.include_router(stock_chart.router, prefix="/api/v1")  # stock_chart 라우터 prefix 추가
app.include_router(return_analysis.router, prefix="/api/v1", tags=["return-analysis"])
app.include_router(intention, prefix="/api/v1", tags=["intention"])  # intention_api 라우터 prefix 추가
app.include_router(industry.router, prefix="/api/v1")  # industry 라우터 prefix 추가
app.include_router(clients.router, prefix="/api/v1", tags=["clients"])  # clients 라우터 추가
app.include_router(portfolio_charts.router, prefix="/api/v1", tags=["portfolio-charts"])  # portfolio_charts 라우터 추가

@app.get("/")
def read_root():
    return {"Hello": "World"}