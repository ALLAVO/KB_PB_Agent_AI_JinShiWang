import requests
import time
import os
import json
import yfinance as yf

# 요청 간 최소 대기시간 (초 단위)
RATE_LIMIT_SLEEP = 2

##### 01. 제무재표 #####
# CIK 캐시 파일 경로
def get_cik_for_ticker(ticker: str) -> str:
    """
    cik_cache.json에서 티커에 해당하는 CIK를 반환합니다. 없으면 None 반환.
    """
    cache_path = os.path.join(os.path.dirname(__file__), 'cik_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            try:
                cache = json.load(f)
            except Exception:
                cache = {}
        cik = cache.get(ticker.lower())
        if cik:
            return str(cik).zfill(10)
    return None

# SEC XBRL companyfacts API에서 주요 재무제표(Income Statement, Balance Sheet, Cash Flow Statement)를 추출하는 함수

def get_financial_statements_from_sec(ticker: str, start_date: str = None, end_date: str = None) -> dict:
    """
    SEC XBRL companyfacts API에서 요청한 주요 재무제표 항목(XBRL Tag 기준)만 반환합니다.
    start_date, end_date: YYYY-MM-DD (주차의 시작일, 마지막날)
    구간 내(end 기준)에 있는 값이 있으면 그 값을, 없으면 구간과 가장 가까운 값을 반환합니다.
    """
    from datetime import datetime
    cik = get_cik_for_ticker(ticker)
    if not cik:
        return {"error": f"CIK not found for ticker {ticker}"}

    company_facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        resp = requests.get(
            company_facts_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MyApp/1.0; +contact@email.com)"}
        )
        time.sleep(RATE_LIMIT_SLEEP)
        if resp.status_code != 200:
            return {"error": f"Failed to fetch company facts for CIK {cik}: Status {resp.status_code}"}
        data = resp.json()
        us_gaap = data.get('facts', {}).get('us-gaap', {})
        tags = [
            'Revenues',
            'SalesRevenueNet',
            'CostOfRevenue',
            'CostOfGoodsAndServicesSold',
            'SellingGeneralAndAdministrativeExpenses',
            'OperatingIncomeLoss',
            'NetIncomeLoss',
            'EarningsPerShareBasic',
            'Assets',
            'Liabilities',
            'StockholdersEquity',
            'AssetsCurrent',
            'LiabilitiesCurrent',
            'Inventory',
            'AccountsReceivableNet',
            'NetCashProvidedByUsedInOperatingActivities',
            'NetCashProvidedByUsedInInvestingActivities',
            'NetCashProvidedByUsedInFinancingActivities',
            'CashAndCashEquivalentsAtCarryingValue',
            'CommonStockSharesOutstanding',
            'DividendsPerShareDeclared'
        ]
        # 날짜 파싱
        dt_start = None
        dt_end = None
        if start_date:
            try:
                dt_start = datetime.strptime(start_date, "%Y-%m-%d")
            except Exception:
                pass
        if end_date:
            try:
                dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            except Exception:
                pass
        result = {}
        for tag in tags:
            value = None
            value_date = None
            if tag in us_gaap:
                facts = us_gaap[tag].get('units', {})
                unit = 'USD' if 'USD' in facts else (list(facts.keys())[0] if facts else None)
                if unit:
                    fact_list = facts[unit]
                    # end 필드가 있는 값만 필터링
                    filtered = [f for f in fact_list if 'end' in f]
                    # 1. 구간 내 값이 있으면 그 중 가장 가까운 값
                    if dt_start and dt_end and filtered:
                        in_range = [f for f in filtered if dt_start <= datetime.strptime(f['end'], "%Y-%m-%d") <= dt_end]
                        if in_range:
                            # 구간 내에서 end가 start_date에 가장 가까운 값
                            closest = min(in_range, key=lambda f: abs((datetime.strptime(f['end'], "%Y-%m-%d") - dt_start).days))
                            value = closest['val']
                            value_date = closest['end']
                        else:
                            # 구간 밖이면 start/end 중 더 가까운 값
                            closest = min(filtered, key=lambda f: min(abs((datetime.strptime(f['end'], "%Y-%m-%d") - dt_start).days), abs((datetime.strptime(f['end'], "%Y-%m-%d") - dt_end).days)))
                            value = closest['val']
                            value_date = closest['end']
                    else:
                        # 날짜 인풋 없으면 최신값
                        value = fact_list[0]['val']
                        value_date = fact_list[0].get('end')
            result[tag] = {"value": value, "date": value_date}
        return result
    except Exception as e:
        return {"error": f"Error fetching or parsing company facts: {e}"}
    

#### 02 . 회사 정보 #####  ---- 이 부분 수정하기!!!!
def get_company_profile_from_yahoo(ticker: str, max_retries: int = 10, sleep_sec: int = 2) -> dict:
    """
    Yahoo Finance API를 통해 기업의 기본 정보를 반환합니다.
    rate limit 발생 시 재시도하며, 요청 간 sleep을 둡니다.
    반환: {
        business_summary: "기업의 사업 개요",
    }
    """
    import time
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # 최소 필수 정보가 있으면 반환
            if info.get("longName") or info.get("shortName"):
                return {
                    "business_summary": info.get("longBusinessSummary"),
                }
            # 데이터가 없으면 에러
            else:
                raise Exception("No company info returned from Yahoo Finance.")
        except Exception as e:
            # rate limit 또는 기타 에러 발생 시 재시도
            if attempt < max_retries - 1:
                time.sleep(sleep_sec * (attempt + 1))  # 점진적으로 대기 시간 증가
            else:
                return {"error": f"Error fetching Yahoo Finance company profile: {e}"}


#### 03 . 주가 + 기술지표 #####

def get_weekly_stock_indicators_from_yahoo(ticker: str, start_date: str, end_date: str) -> dict:
    """
    Yahoo Finance에서 주간 주가(종가, 시가, 고가, 저가, 거래량)와 기술지표(5/10/20일 이동평균, 주간 변동성 등)를 반환합니다.
    start_date, end_date: 'YYYY-MM-DD' (주차의 시작일, 마지막날)
    반환: {
        'close_avg', 'open_avg', 'high_avg', 'low_avg', 'volume_avg',
        'ma5', 'ma10', 'ma20', 'volatility', 'price_change_pct'
    }
    """
    import pandas as pd
    import numpy as np
    try:
        stock = yf.Ticker(ticker)
        # 주간 데이터 가져오기
        df = stock.history(start=start_date, end=end_date, interval='1d')
        if df.empty:
            return {"error": "No price data in given period."}
        # 주간 평균
        close_avg = df['Close'].mean()
        open_avg = df['Open'].mean()
        high_avg = df['High'].mean()
        low_avg = df['Low'].mean()
        volume_avg = df['Volume'].mean()
        # 이동평균 (과거 데이터 포함, 주간 마지막날 기준)
        df_ma = stock.history(end=end_date, period='30d', interval='1d')
        ma5 = df_ma['Close'].rolling(window=5).mean().iloc[-1] if len(df_ma) >= 5 else None
        ma10 = df_ma['Close'].rolling(window=10).mean().iloc[-1] if len(df_ma) >= 10 else None
        ma20 = df_ma['Close'].rolling(window=20).mean().iloc[-1] if len(df_ma) >= 20 else None
        # 주간 변동성 (표준편차)
        volatility = df['Close'].std()
        # 주간 등락률
        price_change_pct = ((df['Close'][-1] - df['Close'][0]) / df['Close'][0]) * 100 if len(df['Close']) > 1 else None
        return {
            'close_avg': close_avg,
            'open_avg': open_avg,
            'high_avg': high_avg,
            'low_avg': low_avg,
            'volume_avg': volume_avg,
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'volatility': volatility,
            'price_change_pct': price_change_pct
        }
    except Exception as e:
        return {"error": f"Error fetching Yahoo Finance stock indicators: {e}"}
