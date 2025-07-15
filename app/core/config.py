# 환경설정 및 환경변수 관리
from pydantic import Field
from pydantic_settings import BaseSettings

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

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"

settings = Settings()
