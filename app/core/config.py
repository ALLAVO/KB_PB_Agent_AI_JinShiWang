# 환경설정 및 환경변수 관리
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "KB Jinshiwang API"
    # 여기에 필요한 다른 설정들을 추가합니다.
    # 예: DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
