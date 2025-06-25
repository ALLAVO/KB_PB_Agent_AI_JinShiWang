import psycopg2
from sqlalchemy import create_engine
from app.core.config import settings

def check_db_connection():
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        return None

def get_sqlalchemy_engine():
    db_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    return create_engine(db_url)
