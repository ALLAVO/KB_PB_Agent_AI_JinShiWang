# 환경설정 및 환경변수 관리
from pydantic import Field
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    APP_NAME: str = "KB Jinshiwang API"

    # 데이터베이스 설정
    DB_HOST: str
    DB_PORT: int = 5432  # 기본값 설정
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # API KEY 설정
    FRED_API_KEY: str
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    FMP_API_KEY: str = Field(..., env="FMP_API_KEY")

    # Cache Settings
    cache_dir: str = "/app/cache"
    mcdonald_cache_enabled: bool = True
    cache_expiry_hours: int = 168
    alphavantage_api_key: str = ""

    @property
    def DATABASE_URL(self) -> str:
        # Cloud SQL Unix socket 연결 (Cloud Run 환경)
        # DB_HOST가 /cloudsql/ 로 시작하는지 확인
        if self.DB_HOST and self.DB_HOST.startswith("/cloudsql/"):
            # 올바른 DSN 형식: postgresql+psycopg2://<user>:<password>@/<db_name>?host=/cloudsql/<instance_connection_name>
            db_url = (
                f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@/{self.DB_NAME}"
                f"?host={self.DB_HOST}"
            )
            print(f"Using Cloud SQL Unix socket: {self.DB_HOST}")
            return db_url
        
        # 일반 TCP 연결 (로컬 개발환경)
        db_url = f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        print(f"Using TCP connection: {self.DB_HOST}")
        return db_url

    class Config:
        env_file = ".env"
        # .env 파일이 없을 경우를 대비하여 extra 설정 추가
        extra = 'ignore'

settings = Settings()