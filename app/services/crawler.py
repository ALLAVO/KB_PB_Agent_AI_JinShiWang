import requests
import time
import os
import json
import yfinance as yf
import pandas_datareader.data as web
from app.core.config import settings

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
                            # 구간 밖이면 dt_end 이전(과거) 값 중 가장 가까운 값만 반환
                            past = [f for f in filtered if datetime.strptime(f['end'], "%Y-%m-%d") < dt_start]
                            if past:
                                closest = max(past, key=lambda f: datetime.strptime(f['end'], "%Y-%m-%d"))
                                value = closest['val']
                                value_date = closest['end']
                            else:
                                value = None
                                value_date = None
                    else:
                        # 날짜 인풋 없으면 최신값
                        value = fact_list[0]['val']
                        value_date = fact_list[0].get('end')
            result[tag] = {"value": value, "date": value_date}
        return result
    except Exception as e:
        return {"error": f"Error fetching or parsing company facts: {e}"}
    

#### 02 . 회사 정보 #####
def get_company_profile_from_alphavantage(ticker: str, api_key: str) -> dict:
    """
    Alpha Vantage Company Overview API를 통해 기업의 name, sector, industry, description, address를 반환합니다.
    """
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            return {"error": f"Alpha Vantage API request failed: {resp.status_code}"}
        data = resp.json()
        # Alpha Vantage는 데이터가 없으면 빈 dict 반환
        if not data or 'Note' in data or 'Error Message' in data:
            return {"error": f"No data or rate limited: {data.get('Note', data.get('Error Message', 'No data'))}"}
        return {
            "company_name": data.get("Name"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "address": data.get("Address"),
            "description": data.get("Description")
        }
    except Exception as e:
        return {"error": f"Error fetching Alpha Vantage company profile: {e}"}


#### 03 . 주가 + 기술지표 #####

def get_weekly_stock_indicators_from_stooq(ticker: str, start_date: str, end_date: str) -> dict:
    """
    Stooq에서 주간 주가(종가, 시가, 고가, 저가, 거래량)와 기술지표(주간 변동성 등)를 반환합니다.
    start_date, end_date: 'YYYY-MM-DD' (주차의 시작일, 마지막날)
    반환: {
        'close_avg', 'open_avg', 'high_avg', 'low_avg', 'volume_avg',
        'volatility', 'price_change_pct'
    }
    """
    import pandas as pd
    import pandas_datareader.data as web
    try:
        if not ticker.endswith('.US'):
            ticker = ticker + '.US'
        df = web.DataReader(ticker, 'stooq', start=start_date, end=end_date)
        if df.empty:
            return {"error": "No price data in given period."}
        df = df.sort_index()  # 날짜 오름차순
        close_avg = df['Close'].mean()
        open_avg = df['Open'].mean()
        high_avg = df['High'].mean()
        low_avg = df['Low'].mean()
        volume_avg = df['Volume'].mean()
        volatility = df['Close'].std()
        price_change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100 if len(df['Close']) > 1 else None
        return {
            'close_avg': close_avg,
            'open_avg': open_avg,
            'high_avg': high_avg,
            'low_avg': low_avg,
            'volume_avg': volume_avg,
            'volatility': volatility,
            'price_change_pct': price_change_pct
        }
    except Exception as e:
        return {"error": f"Error fetching stock indicators from Stooq: {e}"}

def get_moving_averages_from_stooq(ticker: str, end_date: str, windows=[5, 10, 20]) -> dict:
    """
    Stooq에서 end_date 기준 과거 30일간의 종가로 이동평균(MA5, MA10, MA20)을 계산합니다.
    반환: {'ma5': ..., 'ma10': ..., 'ma20': ...}
    """
    import pandas as pd
    import pandas_datareader.data as web
    try:
        if not ticker.endswith('.US'):
            ticker = ticker + '.US'
        # 30일치 데이터 확보
        df = web.DataReader(ticker, 'stooq', end=end_date, start=None)
        df = df.sort_index()
        result = {}
        for w in windows:
            if len(df) >= w:
                result[f'ma{w}'] = df['Close'].rolling(window=w).mean().iloc[-1]
            else:
                result[f'ma{w}'] = None
        return result
    except Exception as e:
        return {"error": f"Error calculating moving averages from Stooq: {e}"}

# 기존 Yahoo 함수 대체
get_weekly_stock_indicators_from_yahoo = get_weekly_stock_indicators_from_stooq


#### 04 . 시황정보 : 증시, 채권, 환율 #####

## 04-1. 미국 증시 지수
def get_us_stock_indices_range(start_date: str, end_date: str) -> dict:
    """
    Stooq를 이용해 미국 증시(Dow, S&P500, Nasdaq) 지수의 기간별(시작~끝) 평균 종가를 반환합니다.
    """
    try:
        dow_hist = web.DataReader('^DJI', 'stooq', start=start_date, end=end_date)
        sp500_hist = web.DataReader('^SPX', 'stooq', start=start_date, end=end_date)
        nasdaq_hist = web.DataReader('^NDQ', 'stooq', start=start_date, end=end_date)
        return {
            'dow_avg': float(dow_hist['Close'].mean()) if not dow_hist.empty else None,
            'sp500_avg': float(sp500_hist['Close'].mean()) if not sp500_hist.empty else None,
            'nasdaq_avg': float(nasdaq_hist['Close'].mean()) if not nasdaq_hist.empty else None
        }
    except Exception as e:
        return {"error": f"Error fetching US stock indices (range) from Stooq: {e}"}


# ## 04-2. 미국 국채 금리
def get_us_treasury_yields_range(fred_api_key: str, start_date: str, end_date: str) -> dict:
    """
    FRED API를 이용해 미국 국채 2년물(DGS2), 10년물(DGS10) 기간별(시작~끝) 평균 금리를 반환합니다.
    """
    import pandas as pd
    try:
        url_2y = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS2&api_key={fred_api_key}&file_type=json&observation_start={start_date}&observation_end={end_date}"
        url_10y = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={fred_api_key}&file_type=json&observation_start={start_date}&observation_end={end_date}"
        resp_2y = requests.get(url_2y)
        resp_10y = requests.get(url_10y)
        obs_2y = resp_2y.json().get('observations', [])
        obs_10y = resp_10y.json().get('observations', [])
        vals_2y = [float(o['value']) for o in obs_2y if o['value'] not in ('.', None, '')]
        vals_10y = [float(o['value']) for o in obs_10y if o['value'] not in ('.', None, '')]
        return {
            'us_2y_avg': float(pd.Series(vals_2y).mean()) if vals_2y else None,
            'us_10y_avg': float(pd.Series(vals_10y).mean()) if vals_10y else None
        }
    except Exception as e:
        return {"error": f"Error fetching US treasury yields (range): {e}"}


# 04-3. 한국 환율
def get_kr_fx_rates_range(_: str, start_date: str, end_date: str) -> dict:
    """
    Frankfurter API를 이용해 USD/KRW, EUR/KRW 환율의 기간별(시작~끝) 평균값을 반환합니다.
    API Key 불필요.
    """
    import pandas as pd
    try:
        url_usd = f"https://api.frankfurter.app/{start_date}..{end_date}?from=USD&to=KRW"
        url_eur = f"https://api.frankfurter.app/{start_date}..{end_date}?from=EUR&to=KRW"
        resp_usd = requests.get(url_usd)
        resp_usd.raise_for_status()
        data_usd = resp_usd.json().get('rates', {})
        vals_usd = [v['KRW'] for v in data_usd.values() if v.get('KRW')]
        resp_eur = requests.get(url_eur)
        resp_eur.raise_for_status()
        data_eur = resp_eur.json().get('rates', {})
        vals_eur = [v['KRW'] for v in data_eur.values() if v.get('KRW')]
        return {
            'usd_krw_avg': float(pd.Series(vals_usd).mean()) if vals_usd else None,
            'eur_krw_avg': float(pd.Series(vals_eur).mean()) if vals_eur else None
        }
    except Exception as e:
        return {"error": f"Error fetching KR FX rates from Frankfurter API: {e}"}

