import psycopg2
from sqlalchemy import create_engine
from app.core.config import settings

def check_db_connection():
    try:
        print("DB_HOST:", settings.DB_HOST)  # 환경 변수 값 확인용
        if settings.DB_HOST.startswith("/cloudsql/"):
            # Unix socket connection (Cloud SQL)
            conn = psycopg2.connect(
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
            )
        else:
            # TCP connection
            conn = psycopg2.connect(
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
            )
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        return None

def get_sqlalchemy_engine():
    if settings.DB_HOST.startswith("/cloudsql/"):
        # Cloud SQL Unix socket - 올바른 형식으로 수정
        db_url = (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@/{settings.DB_NAME}?"
            f"unix_sock={settings.DB_HOST}/.s.PGSQL.5432"
        )
        print("Cloud SQL URL:", db_url)  # 디버깅용
    else:
        db_url = (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        print("TCP URL:", db_url)  # 디버깅용
    return create_engine(db_url)