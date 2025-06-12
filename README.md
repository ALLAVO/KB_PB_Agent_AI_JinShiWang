# KB Jinshiwang Project

PB(Private Banker)를 위한 증시 분석 AI 에이전트 프로젝트입니다.

## 프로젝트 목적
- 기업 현황 분석을 중심으로 증시 분석 AI 에이전트 개발

## 주요 기능
1.  **고객 정보 입력**: 투자 포트폴리오, 투자 성향, 고객 성함, 담당 PB 등
2.  **DB 구축 및 정제**: 기존 기업 DB(주가, 뉴스 데이터) 연동 및 뉴스 감성 점수화
3.  **주가 방향 예측**: LSTM 모델 활용 (상승, 유지, 하락)
4.  **보고서 생성 (GPT 활용)**:
    *   고객 매수 기업 정보 (Yahoo Finance 크롤링)
    *   주가 방향 예측 결과
    *   예측 근거 설명
    *   기업별 금주 하이라이트 뉴스

## 기술 스택
- Backend: FastAPI
- Database: (추후 명시)
- ML Model: LSTM (기존 모델 활용)
- NLP: (뉴스 감성 분석 모델), GPT (보고서 생성)

## 디렉토리 구조

```
kb_jinshiwang/
│
├── app/                   # FastAPI 백엔드 애플리케이션
│   ├── main.py            # FastAPI 앱 실행 엔트리포인트
│   ├── api/               # API 라우터 (company, customer, prediction, report, sentiment)
│   ├── core/              # 설정, 환경변수, 보안 (config.py 등)
│   ├── db/                # DB 연결, 모델, CRUD, 시드 데이터
│   ├── schemas/           # Pydantic 데이터 모델
│   ├── services/          # 비즈니스 로직, 크롤러, 리포트 생성 등
│   ├── utils/             # 공통 유틸 함수
│   └── dependencies.py    # FastAPI 의존성 주입 함수
│
├── frontend/              # React 프론트엔드 (Create React App 기반)
│   ├── public/            # 정적 파일 (index.html 등)
│   ├── src/               # React 소스 코드
│   ├── build/             # 빌드 결과물
│   ├── package.json       # 프론트엔드 패키지 관리
│   └── README.md          # 프론트엔드 설명
│
├── tests/                 # 백엔드 테스트 코드
├── requirements.txt       # Python 패키지 목록
├── .env                   # 환경변수 파일 (API 키 등)
├── README.md              # 프로젝트 설명
└── .gitignore             # Git 무시 파일
```

## 실행 방법

### 백엔드 (FastAPI)
```zsh
uvicorn app.main:app --reload
```

### 프론트엔드 (React)
```zsh
cd frontend
npm install
npm start
```

## 환경 변수 설정 (.env 예시)
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=youruser
DB_PASSWORD=yourpassword
ALPHAVANTAGE_API_KEY=... # Alpha Vantage API 키
FRED_API_KEY=...         # FRED API 키
```

## 주요 서비스/크롤러 설명
- app/services/crawler.py: SEC, Yahoo Finance, Alpha Vantage, Stooq, FRED, Frankfurter API 등 다양한 소스에서 재무/시장/환율 데이터 수집 및 평균값 반환, 에러 핸들링 및 API Key 관리 포함
- .env 및 app/core/config.py: 모든 API Key 및 환경변수 관리

## 테스트
- 각 서비스 함수는 python3 -c "from app.services.crawler import ...; print(...())" 형태로 직접 테스트 가능
- tests/ 디렉토리의 pytest 기반 테스트 코드 포함

---

자세한 사용법, API 명세, 데이터 예시는 각 모듈/코드 내 docstring 참고
