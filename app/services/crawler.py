# Yahoo Finance 등 외부 데이터 크롤링
import yfinance as yf
# from app.schemas.company import CompanyInfo # 크롤링한 데이터를 저장할 스키마
import requests
from datetime import datetime
import os
import json

CIK_CACHE_PATH = os.path.join(os.path.dirname(__file__), 'cik_cache.json')

def load_cik_cache():
    if os.path.exists(CIK_CACHE_PATH):
        with open(CIK_CACHE_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_cik_cache(cache):
    with open(CIK_CACHE_PATH, 'w') as f:
        json.dump(cache, f)

def get_cik_for_ticker(ticker: str) -> str:
    cache = load_cik_cache()
    ticker_lower = ticker.lower()
    if ticker_lower in cache:
        return cache[ticker_lower]
    # 캐시에 없으면 SEC에서 한 번만 시도
    cik_lookup_url = f"https://www.sec.gov/files/company_tickers.json"
    try:
        resp = requests.get(cik_lookup_url, headers={"User-Agent": "Mozilla/5.0 (your_email@example.com)"})
        if resp.status_code == 200:
            data = resp.json()
            for v in data.values():
                if v['ticker'].lower() == ticker_lower:
                    cik = str(v['cik_str']).zfill(10)
                    cache[ticker_lower] = cik
                    save_cik_cache(cache)
                    return cik
    except Exception:
        pass
    return None

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

def get_edgar_financials(ticker: str, date: str = None):
    """
    SEC EDGAR에서 입력한 날짜(date)에 유효한 최신 10-K/10-Q 보고서의 재무제표를 반환합니다.
    date: YYYY-MM-DD (optional, 없으면 오늘)
    """
    cik = get_cik_for_ticker(ticker)
    if not cik:
        return {"error": f"CIK not found for ticker {ticker}"}
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = datetime.now()
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = requests.get(submissions_url, headers={"User-Agent": "Mozilla/5.0 (your_email@example.com)"})
        if resp.status_code != 200:
            return {"error": f"Failed to fetch submissions for CIK {cik}"}
        data = resp.json()
        reports = []
        for filing in data.get('filings', {}).get('recent', {}).get('form', []):
            # 10-K, 10-Q만
            if filing in ("10-K", "10-Q"):
                idx = data['filings']['recent']['form'].index(filing)
                filing_date = data['filings']['recent']['filingDate'][idx]
                report_url = data['filings']['recent']['primaryDocument'][idx]
                accession = data['filings']['recent']['accessionNumber'][idx].replace("-", "")
                # 보고서 제출일이 target_date 이전이어야 함
                if datetime.strptime(filing_date, "%Y-%m-%d") <= target_date:
                    reports.append({
                        "form": filing,
                        "filing_date": filing_date,
                        "accession": accession,
                        "report_url": report_url
                    })
        if not reports:
            return {"error": "No 10-K/10-Q filings found before given date."}
        # 가장 최근 보고서 선택
        latest = sorted(reports, key=lambda x: x['filing_date'], reverse=True)[0]
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{latest['accession']}/{latest['report_url']}"
        return {
            "form": latest['form'],
            "filing_date": latest['filing_date'],
            "report_url": doc_url
        }
    except Exception as e:
        return {"error": f"EDGAR fetch failed: {e}"}

def build_full_cik_cache():
    """
    SEC의 company_tickers.json 전체를 cik_cache.json으로 변환 (모든 ticker→CIK 매핑)
    """
    cik_lookup_url = "https://www.sec.gov/files/company_tickers.json"
    try:
        resp = requests.get(cik_lookup_url, headers={"User-Agent": "Mozilla/5.0 (your_email@example.com)"})
        if resp.status_code == 200:
            data = resp.json()
            cache = {}
            for v in data.values():
                ticker = v['ticker'].lower()
                cik = str(v['cik_str']).zfill(10)
                cache[ticker] = cik
            save_cik_cache(cache)
            print(f"Saved {len(cache)} ticker→CIK pairs to cik_cache.json")
        else:
            print(f"Failed to fetch SEC company_tickers.json: {resp.status_code}")
    except Exception as e:
        print(f"Error building CIK cache: {e}")

pass
