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
├── app/                   # FastAPI 애플리케이션
│   ├── main.py            # FastAPI 앱 실행 엔트리포인트
│   ├── api/               # API 라우터 모음
│   ├── core/              # 설정, 공통 의존성, 보안 등
│   ├── db/                # DB 연결, 모델, CRUD
│   ├── schemas/           # Pydantic 데이터 모델
│   ├── services/          # 비즈니스 로직, 외부 연동
│   ├── utils/             # 공통 유틸 함수
│   └── dependencies.py    # FastAPI 의존성 주입 함수
├── tests/                 # 테스트 코드
├── requirements.txt       # Python 패키지 목록
├── .env                   # 환경변수 파일
├── README.md              # 프로젝트 설명
└── .gitignore             # Git 무시 파일
```

## 실행 방법
(추후 작성)
