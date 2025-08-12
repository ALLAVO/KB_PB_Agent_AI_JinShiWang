# 환경설정 및 환경변수 관리
from pydantic import Field
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    APP_NAME: str = "KB Jinshiwang API"

    # 데이터베이스 설정
    DB_HOST: str
    DB_PORT: int
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
        # 환경변수 DATABASE_URL이 있으면 우선 사용 (Cloud SQL용)
        env_database_url = os.getenv("DATABASE_URL")
        if env_database_url:
            print(f"Using environment DATABASE_URL: {env_database_url}")
            return env_database_url
            
        # Cloud SQL Unix socket 연결 (Cloud Run 환경)
        if self.DB_HOST.startswith("/cloudsql/"):
            db_url = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@/{self.DB_NAME}?host={self.DB_HOST}"
            print(f"Using Cloud SQL Unix socket: {db_url}")
            return db_url
        
        # 일반 TCP 연결 (로컬 개발환경)
        db_url = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        print(f"Using TCP connection: {db_url}")
        return db_url

    class Config:
        env_file = ".env"

settings = Settings()