# FastAPI 앱 실행 엔트리포인트
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import customer, company, prediction, report, sentiment, market

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
app.include_router(company.router, prefix="/api/v1")
app.include_router(prediction.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")  # sentiment 라우터 prefix 추가
app.include_router(market.router, prefix="/api/v1")  # market 라우터 prefix 추가

@app.get("/")
def read_root():
    return {"Hello": "World"}