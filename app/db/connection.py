from app.db.database import engine as main_engine
import os
from sqlalchemy import create_engine
import logging  

logger = logging.getLogger(__name__)

def get_sqlalchemy_engine():
    """SQLAlchemy 엔진을 생성합니다."""
    try:
        # 환경변수에서 DATABASE_URL 가져오기
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            # Cloud SQL 연결 정보로 URL 구성
            db_host = os.getenv('DB_HOST')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME')
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            
            if db_host and db_host.startswith('/cloudsql/'):
                # Cloud SQL Unix 소켓 연결
                database_url = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
            else:
                # TCP 연결
                database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10
        )
        
        return engine
    except Exception as e:
        logger.error(f"Database engine creation error: {e}")
        raise