from sqlalchemy import create_engine
from app.core.config import settings

_engine = None

def get_sqlalchemy_engine():
    """
    SQLAlchemy 엔진 인스턴스를 반환합니다. (싱글톤)
    future=True 옵션을 추가하여 SQLAlchemy 2.x 호환성을 보장합니다.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            future=True  # SQLAlchemy 2.0 스타일 실행 활성화
        )
    return _engine