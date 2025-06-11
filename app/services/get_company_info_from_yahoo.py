import yfinance as yf

def get_company_info_from_yahoo(stock_symbol: str, date: str = None, granularity: str = "year") -> dict:
    """
    Yahoo Finance에서 기업 정보를 조회합니다.
    :param stock_symbol: 주식 심볼 (예: AAPL)
    :param date: 조회 기준 날짜 (YYYY-MM-DD)
    :param granularity: 조회 단위 (day/month/year)
    :return: 기업 정보 딕셔너리
    """
    try:
        ticker = yf.Ticker(stock_symbol)
        info = ticker.info
        if not info or 'shortName' not in info:
            return {"company_name": "정보 없음"}
        result = {
            "company_name": info.get("shortName", "정보 없음"),
            "symbol": info.get("symbol", stock_symbol),
            "sector": info.get("sector", "정보 없음"),
            "industry": info.get("industry", "정보 없음"),
            "country": info.get("country", "정보 없음"),
            "website": info.get("website", "정보 없음"),
            "description": info.get("longBusinessSummary", "정보 없음"),
        }
        return result
    except Exception as e:
        return {"company_name": "정보 없음", "error": str(e)}

