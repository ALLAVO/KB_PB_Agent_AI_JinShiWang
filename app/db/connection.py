import psycopg2
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

