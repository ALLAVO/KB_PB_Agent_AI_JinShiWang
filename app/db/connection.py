from app.db.database import engine as main_engine

def get_sqlalchemy_engine():
    """
    항상 중앙에서 관리되는 SQLAlchemy 엔진을 반환합니다.
    """
    print("Returning the central SQLAlchemy engine.")
    return main_engine