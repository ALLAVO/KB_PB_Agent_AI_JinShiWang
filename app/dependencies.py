# FastAPI 의존성 주입 함수 (DB 세션, 공통 의존성 등)
# from fastapi import Depends, HTTPException, status
# from jose import JWTError, jwt # 예시: JWT 사용 시
# from app.core.config import settings
# from app.db.database import SessionLocal, get_db # DB 세션 가져오기

# def get_current_user():
#     # 여기에 사용자 인증 로직을 구현합니다.
#     # 예: 토큰 검증 등
#     # raise HTTPException(
#     #     status_code=status.HTTP_401_UNAUTHORIZED,
#     #     detail="Not authenticated",
#     #     headers={"WWW-Authenticate": "Bearer"},
#     # )
#     pass

# def common_parameters(q: str = None, skip: int = 0, limit: int = 100):
#     return {"q": q, "skip": skip, "limit": limit}

pass