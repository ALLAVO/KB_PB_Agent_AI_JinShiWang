import psycopg2
from sqlalchemy import create_engine
from app.core.config import settings

def check_db_connection():
    try:
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
        # SQLAlchemy expects the socket path as a query param, not as host
        db_url = (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@/{settings.DB_NAME}?host={settings.DB_HOST}"
        )
    else:
        db_url = (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
    return create_engine(db_url)
