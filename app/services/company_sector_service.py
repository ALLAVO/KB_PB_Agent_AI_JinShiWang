"""
기업 섹터 정보 서비스
"""
import logging
from sqlalchemy import text
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

def get_company_sector_by_ticker(ticker: str) -> dict:
    """
    기업의 ticker로 해당 기업의 섹터 정보를 조회
    
    Args:
        ticker (str): 기업 티커 심볼
        
    Returns:
        dict: 섹터 정보가 포함된 딕셔너리
    """
    db = SessionLocal()
    try:
        # kb_enterprise_dataset 테이블에서 ticker로 섹터 정보 조회
        query = text("""
            SELECT stock_symbol, sector
            FROM kb_enterprise_dataset 
            WHERE stock_symbol = :ticker
            LIMIT 1
        """)
        
        result = db.execute(query, {"ticker": ticker}).fetchone()
        
        if result:
            return {
                "ticker": result[0],
                "sector": result[1]
            }
        else:
            logger.warning(f"No sector data found for ticker: {ticker}")
            return {
                "ticker": ticker,
                "sector": None,
                "message": f"해당 티커({ticker})의 섹터 정보를 찾을 수 없습니다."
            }
                
    except Exception as e:
        logger.error(f"Error fetching company sector for ticker {ticker}: {str(e)}")
        raise Exception(f"기업 섹터 정보 조회 중 오류가 발생했습니다: {str(e)}")
    finally:
        db.close()
