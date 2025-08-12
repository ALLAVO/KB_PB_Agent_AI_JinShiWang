import psycopg2
from sqlalchemy import create_engine
from app.core.config import settings
from app.db.database import engine as main_engine # 중앙 엔진을 가져옴

def check_db_connection():
    """
    중앙 SQLAlchemy 엔진을 사용하여 데이터베이스 연결을 확인합니다.
    """
    try:
        print("Checking DB connection using the central engine...")
        # 엔진에서 직접 연결을 가져와 테스트
        conn = main_engine.connect()
        conn.close()
        print("Database connection successful.")
        return True
    except Exception as e:
        print(f"Error connecting to the database via engine: {e}")
        return False

def get_sqlalchemy_engine():
    """
    항상 중앙에서 관리되는 SQLAlchemy 엔진을 반환합니다.
    새 엔진을 만들지 않습니다.
    """
    print("Returning the central SQLAlchemy engine.")
    return main_engine