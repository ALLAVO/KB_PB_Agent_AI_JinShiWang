# Yahoo Finance 등 외부 데이터 크롤링
import yfinance as yf
# from app.schemas.company import CompanyInfo # 크롤링한 데이터를 저장할 스키마

def get_company_info_from_yahoo(ticker: str, date: str = None, granularity: str = "year") -> dict:
    """
    Yahoo Finance에서 기업 정보를 크롤링합니다.
    date: YYYY-MM-DD 형식 문자열 (optional)
    granularity: 'day', 'month', 'year' 중 하나 (default: 'year')
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # 기본 정보만 추출
        company_name = info.get("longName") or info.get("shortName") or ticker
        industry = info.get("industry")
        sector = info.get("sector")
        business_summary = info.get("longBusinessSummary")
        website = info.get("website")
        address = info.get("address1")
        phone = info.get("phone")
        return {
            "company_name": company_name,
            "stock_symbol": ticker,
            "industry": industry,
            "sector": sector,
            "business_summary": business_summary,
            "website": website,
            "address": address,
            "phone": phone
        }
    except Exception as e:
        return {"company_name": f"{ticker} 정보 없음", "error": str(e)}

def get_technical_indicators(ticker: str, date: str = None) -> dict:
    """
    Yahoo Finance에서 입력한 날짜(date)의 주가 및 주요 기술지표를 반환합니다.
    date: YYYY-MM-DD 형식 문자열 (optional, 없으면 최근 거래일)
    반환: open, high, low, close, volume, SMA_20, RSI_14 등
    """
    import pandas as pd
    import datetime
    try:
        stock = yf.Ticker(ticker)
        if date:
            # 해당 날짜의 데이터만 조회
            df = stock.history(start=date, end=date)
        else:
            # 최근 60일치 데이터 조회 (SMA, RSI 계산용)
            df = stock.history(period="60d")
        if df.empty:
            return {"error": "No data for given date/ticker."}
        # 기준 row: date가 있으면 해당 날짜, 없으면 마지막 row
        if date and date in df.index.strftime("%Y-%m-%d"):
            idx = list(df.index.strftime("%Y-%m-%d")).index(date)
            row = df.iloc[idx]
            df_until = df.iloc[:idx+1]  # SMA, RSI 계산용
        else:
            row = df.iloc[-1]
            df_until = df
        # 단순 이동평균(SMA_20)
        sma_20 = df_until['Close'].rolling(window=20).mean().iloc[-1] if len(df_until) >= 20 else None
        # RSI_14 계산
        delta = df_until['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        rs = roll_up / roll_down
        rsi_14 = 100.0 - (100.0 / (1.0 + rs.iloc[-1])) if roll_down.iloc[-1] != 0 else 100.0
        return {
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
            "SMA_20": float(sma_20) if sma_20 is not None else None,
            "RSI_14": float(rsi_14) if rsi_14 is not None else None
        }
    except Exception as e:
        return {"error": str(e)}

pass
