import requests
import time
import os
import json
import pandas_datareader.data as web
from app.core.config import settings
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import yfinance as yf

# 요청 간 최소 대기시간 (초 단위)
RATE_LIMIT_SLEEP = 10

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

# Stooq에서 주간 주가(종가, 시가, 고가, 저가, 거래량)와 기술지표(주간 변동성 등)를 반환하는 함수
def get_weekly_stock_indicators_from_stooq(ticker: str, start_date: str, end_date: str) -> dict:
    """
    Stooq에서 주간 주가(종가, 시가, 고가, 저가, 거래량)와 기술지표(주간 변동성 등)를 반환합니다.
    start_date, end_date: 'YYYY-MM-DD' (주차의 시작일, 마지막날)
    반환: {
        'close_avg', 'open_avg', 'high_avg', 'low_avg', 'volume_avg',
        'volatility', 'price_change_pct'
    }
    """
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

def get_stock_price_chart_data(ticker: str, start_date: str, end_date: str) -> Dict:
    """
    주식 가격 차트 데이터를 Stooq에서 가져옵니다.
    """
    try:
        if not ticker.endswith('.US'):
            ticker = ticker + '.US'
        df = web.DataReader(ticker, 'stooq', start=start_date, end=end_date)
        if df.empty:
            return {"error": f"No data found for symbol {ticker}"}
        df = df.sort_index()
        return {
            "dates": [date.strftime('%Y-%m-%d') for date in df.index],
            "closes": df['Close'].tolist(),
            "opens": df['Open'].tolist(),
            "highs": df['High'].tolist(),
            "lows": df['Low'].tolist(),
            "volumes": df['Volume'].tolist()
        }
    except Exception as e:
        return {"error": f"Error fetching stock data from Stooq for {ticker}: {e}"}

def get_stock_price_chart_with_ma(ticker: str, start_date: str, end_date: str, ma_periods: List[int]) -> Dict:
    """
    이동평균이 포함된 주식 가격 차트 데이터를 Stooq에서 가져옵니다.
    """
    try:
        if not ticker.endswith('.US'):
            ticker = ticker + '.US'
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        extended_start = start_dt - timedelta(days=max(ma_periods) + 30)
        df = web.DataReader(ticker, 'stooq', start=extended_start.strftime('%Y-%m-%d'), end=end_date)
        if df.empty:
            return {"error": f"No data found for symbol {ticker}"}
        df = df.sort_index()
        for period in ma_periods:
            df[f'ma{period}'] = df['Close'].rolling(window=period).mean()
        filtered_df = df[df.index >= start_date]
        if filtered_df.empty:
            return {"error": f"No data in specified date range for {ticker}"}
        result = {
            "dates": [date.strftime('%Y-%m-%d') for date in filtered_df.index],
            "closes": filtered_df['Close'].tolist()
        }
        for period in ma_periods:
            ma_key = f"ma{period}"
            result[ma_key] = filtered_df[ma_key].tolist()
        return result
    except Exception as e:
        return {"error": f"Error fetching MA data from Stooq for {ticker}: {e}"}

def get_index_chart_data(symbol: str, start_date: str, end_date: str) -> Dict:
    """
    지수 데이터를 Stooq에서 가져옵니다 (나스닥, S&P 500 등)
    """
    try:
        # Stooq는 미국 지수는 심볼 그대로 사용
        df = web.DataReader(symbol, 'stooq', start=start_date, end=end_date)
        if df.empty:
            return {"error": f"No data found for symbol {symbol}"}
        df = df.sort_index()
        return {
            "dates": [date.strftime('%Y-%m-%d') for date in df.index],
            "closes": df['Close'].tolist(),
            "opens": df['Open'].tolist(),
            "highs": df['High'].tolist(),
            "lows": df['Low'].tolist(),
            "volumes": df['Volume'].tolist()
        }
    except Exception as e:
        return {"error": f"Error fetching index data from Stooq for {symbol}: {e}"}

def get_nasdaq_index_data(start_date: str, end_date: str) -> dict:
    """
    나스닥 지수 데이터를 가져옵니다.
    start_date, end_date: 'YYYY-MM-DD'
    반환: {
        'dates': [...],
        'nasdaq_closes': [...]
    }
    """
    try:
        df = web.DataReader('^NDQ', 'stooq', start=start_date, end=end_date)
        if df.empty:
            return {"error": "No NASDAQ data in given period."}
        df = df.sort_index()  # 날짜 오름차순
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in df.index],
            'nasdaq_closes': df['Close'].tolist()
        }
    except Exception as e:
        return {"error": f"Error fetching NASDAQ data from Stooq: {e}"}

def calculate_absolute_and_relative_returns(ticker: str, start_date: str, end_date: str) -> dict:
    """
    개별 주식의 절대수익률과 나스닥 대비 상대수익률을 계산합니다.
    start_date, end_date: 'YYYY-MM-DD'
    반환: {
        'dates': [...],
        'stock_prices': [...],
        'nasdaq_prices': [...],
        'stock_index': [...],      # 기준일=100으로 정규화
        'nasdaq_index': [...],     # 기준일=100으로 정규화
        'relative_index': [...],   # 상대지수
        'stock_returns': [...],    # 수익률(%)
        'nasdaq_returns': [...],   # 수익률(%)
        'relative_returns': [...]  # 상대수익률(%)
    }
    """
    try:
        # 개별 주식 데이터 가져오기
        stock_data = get_stock_price_chart_data(ticker, start_date, end_date)
        if "error" in stock_data:
            return stock_data
        
        # 나스닥 데이터 가져오기
        nasdaq_data = get_nasdaq_index_data(start_date, end_date)
        if "error" in nasdaq_data:
            return nasdaq_data
        
        # 날짜 매칭 (두 데이터의 교집합)
        stock_dates = set(stock_data['dates'])
        nasdaq_dates = set(nasdaq_data['dates'])
        common_dates = sorted(list(stock_dates & nasdaq_dates))
        
        if not common_dates:
            return {"error": "No common dates between stock and NASDAQ data"}
        
        # 공통 날짜에 해당하는 데이터만 추출
        stock_prices = []
        nasdaq_prices = []
        
        for date in common_dates:
            stock_idx = stock_data['dates'].index(date)
            nasdaq_idx = nasdaq_data['dates'].index(date)
            stock_prices.append(stock_data['closes'][stock_idx])
            nasdaq_prices.append(nasdaq_data['nasdaq_closes'][nasdaq_idx])
        
        # 지수 계산 (기준일=100)
        stock_index = [(price / stock_prices[0]) * 100 for price in stock_prices]
        nasdaq_index = [(price / nasdaq_prices[0]) * 100 for price in nasdaq_prices]
        
        # 상대지수 계산
        relative_index = [(s_idx / n_idx) * 100 for s_idx, n_idx in zip(stock_index, nasdaq_index)]
        
        # 수익률 계산 (%)
        stock_returns = [((price / stock_prices[0]) - 1) * 100 for price in stock_prices]
        nasdaq_returns = [((price / nasdaq_prices[0]) - 1) * 100 for price in nasdaq_prices]
        relative_returns = [((rel_idx / 100) - 1) * 100 for rel_idx in relative_index]
        
        return {
            'dates': common_dates,
            'stock_prices': stock_prices,
            'nasdaq_prices': nasdaq_prices,
            'stock_index': stock_index,
            'nasdaq_index': nasdaq_index,
            'relative_index': relative_index,
            'stock_returns': stock_returns,
            'nasdaq_returns': nasdaq_returns,
            'relative_returns': relative_returns
        }
        
    except Exception as e:
        return {"error": f"Error calculating returns: {e}"}

def get_return_analysis_summary(ticker: str, start_date: str, end_date: str) -> dict:
    """
    수익률 분석 요약 정보를 반환합니다.
    """
    try:
        data = calculate_absolute_and_relative_returns(ticker, start_date, end_date)
        if "error" in data:
            return data
        
        if not data['stock_returns']:
            return {"error": "No return data available"}
        
        stock_final_return = data['stock_returns'][-1]
        nasdaq_final_return = data['nasdaq_returns'][-1]
        relative_final_return = data['relative_returns'][-1]
        
        # 변동성 계산 (일간 수익률의 표준편차 × √252)
        import numpy as np
        if len(data['stock_prices']) > 1:
            daily_stock_returns = [((data['stock_prices'][i] / data['stock_prices'][i-1]) - 1) * 100 
                                 for i in range(1, len(data['stock_prices']))]
            stock_volatility = np.std(daily_stock_returns) * (252 ** 0.5)
        else:
            stock_volatility = 0
        
        return {
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "stock_return": round(stock_final_return, 2),
            "nasdaq_return": round(nasdaq_final_return, 2),
            "relative_return": round(relative_final_return, 2),
            "stock_volatility": round(stock_volatility, 2),
            "outperformance": round(stock_final_return - nasdaq_final_return, 2),
            "data_points": len(data['dates'])
        }
        
    except Exception as e:
        return {"error": f"Error generating return analysis summary: {e}"}


#### 04 . 시황정보 : 증시, 채권, 환율 #####

## 04-1. 미국 증시 지수
def get_us_indices_6months_chart(end_date: str) -> dict:
    """
    DOW, S&P500, NASDAQ 6개월치 일별 종가 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (그래프 마지막 날짜)
    반환: {
        'dow': {'dates': [...], 'closes': [...]},
        'sp500': {'dates': [...], 'closes': [...]},
        'nasdaq': {'dates': [...], 'closes': [...]}
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=182)  # 약 6개월(182일)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')

        indices = {
            'dow': '^DJI',
            'sp500': '^SPX',
            'nasdaq': '^NDQ'
        }
        result = {}
        for key, ticker in indices.items():
            df = web.DataReader(ticker, 'stooq', start=start_str, end=end_str)
            df = df.sort_index()
            if df.empty:
                result[key] = {'dates': [], 'closes': []}
            else:
                result[key] = {
                    'dates': [d.strftime('%Y-%m-%d') for d in df.index],
                    'closes': df['Close'].tolist()
                }
        return result
    except Exception as e:
        return {'error': f'Error fetching 6-month US indices data: {e}'}

def get_us_indices_1year_chart(end_date: str) -> dict:
    """
    DOW, S&P500, NASDAQ 1년치 일별 종가 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (그래프 마지막 날짜)
    반환: {
        'dow': {'dates': [...], 'closes': [...]},
        'sp500': {'dates': [...], 'closes': [...]},
        'nasdaq': {'dates': [...], 'closes': [...]}
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=365)  # 1년(365일)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')

        indices = {
            'dow': '^DJI',
            'sp500': '^SPX',
            'nasdaq': '^NDQ'
        }
        result = {}
        for key, ticker in indices.items():
            df = web.DataReader(ticker, 'stooq', start=start_str, end=end_str)
            df = df.sort_index()
            if df.empty:
                result[key] = {'dates': [], 'closes': []}
            else:
                result[key] = {
                    'dates': [d.strftime('%Y-%m-%d') for d in df.index],
                    'closes': df['Close'].tolist()
                }
        return result
    except Exception as e:
        return {'error': f'Error fetching 1-year US indices data: {e}'}

## 04-2. 미국 국채 금리
def get_us_treasury_yields_6months(fred_api_key: str, end_date: str) -> dict:
    """
    FRED API를 이용해 미국 국채 2년물(DGS2), 10년물(DGS10) 6개월(182일)치 일별 금리 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (마지막 날짜)
    반환: {
        'dates': [...],
        'us_2y': [...],
        'us_10y': [...]
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=182)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')
        url_2y = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS2&api_key={fred_api_key}&file_type=json&observation_start={start_str}&observation_end={end_str}"
        url_10y = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={fred_api_key}&file_type=json&observation_start={start_str}&observation_end={end_str}"
        resp_2y = requests.get(url_2y)
        resp_10y = requests.get(url_10y)
        obs_2y = resp_2y.json().get('observations', [])
        obs_10y = resp_10y.json().get('observations', [])
        dates = [o['date'] for o in obs_2y if o['value'] not in ('.', None, '')]
        us_2y = [float(o['value']) for o in obs_2y if o['value'] not in ('.', None, '')]
        us_10y = [float(o['value']) for o in obs_10y if o['value'] not in ('.', None, '')]
        return {
            'dates': dates,
            'us_2y': us_2y,
            'us_10y': us_10y
        }
    except Exception as e:
        return {'error': f'Error fetching 6-month US treasury yields: {e}'}

def get_us_treasury_yields_1year(fred_api_key: str, end_date: str) -> dict:
    """
    FRED API를 이용해 미국 국채 2년물(DGS2), 10년물(DGS10) 1년(365일)치 일별 금리 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (마지막 날짜)
    반환: {
        'dates': [...],
        'us_2y': [...],
        'us_10y': [...]
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=365)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')
        url_2y = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS2&api_key={fred_api_key}&file_type=json&observation_start={start_str}&observation_end={end_str}"
        url_10y = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={fred_api_key}&file_type=json&observation_start={start_str}&observation_end={end_str}"
        resp_2y = requests.get(url_2y)
        resp_10y = requests.get(url_10y)
        obs_2y = resp_2y.json().get('observations', [])
        obs_10y = resp_10y.json().get('observations', [])
        dates = [o['date'] for o in obs_2y if o['value'] not in ('.', None, '')]
        us_2y = [float(o['value']) for o in obs_2y if o['value'] not in ('.', None, '')]
        us_10y = [float(o['value']) for o in obs_10y if o['value'] not in ('.', None, '')]
        return {
            'dates': dates,
            'us_2y': us_2y,
            'us_10y': us_10y
        }
    except Exception as e:
        return {'error': f'Error fetching 1-year US treasury yields: {e}'}


# 04-3. 한국 환율
def get_kr_fx_rates_6months(end_date: str) -> dict:
    """
    Frankfurter API를 이용해 USD/KRW, EUR/KRW 환율의 6개월(182일)치 일별 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (마지막 날짜)
    반환: {
        'dates': [...],
        'usd_krw': [...],
        'eur_usd': [...]
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=182)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')
        url_usd = f"https://api.frankfurter.app/{start_str}..{end_str}?from=USD&to=KRW"
        url_eur = f"https://api.frankfurter.app/{start_str}..{end_str}?from=EUR&to=USD"
        resp_usd = requests.get(url_usd)
        resp_usd.raise_for_status()
        data_usd = resp_usd.json().get('rates', {})
        resp_eur = requests.get(url_eur)
        resp_eur.raise_for_status()
        data_eur = resp_eur.json().get('rates', {})
        dates = sorted(list(set(data_usd.keys()) | set(data_eur.keys())))
        usd_krw = [data_usd.get(date, {}).get('KRW') for date in dates]
        eur_usd = [data_eur.get(date, {}).get('USD') for date in dates]
        return {
            'dates': dates,
            'usd_krw': usd_krw,
            'eur_usd': eur_usd
        }
    except Exception as e:
        return {'error': f'Error fetching 6-month KR FX rates: {e}'}

def get_kr_fx_rates_1year(end_date: str) -> dict:
    """
    Frankfurter API를 이용해 USD/KRW, EUR/KRW 환율의 1년(365일)치 일별 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (마지막 날짜)
    반환: {
        'dates': [...],
        'usd_krw': [...],
        'eur_usd': [...]
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=365)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')
        url_usd = f"https://api.frankfurter.app/{start_str}..{end_str}?from=USD&to=KRW"
        url_eur = f"https://api.frankfurter.app/{start_str}..{end_str}?from=EUR&to=USD"
        resp_usd = requests.get(url_usd)
        resp_usd.raise_for_status()
        data_usd = resp_usd.json().get('rates', {})
        resp_eur = requests.get(url_eur)
        resp_eur.raise_for_status()
        data_eur = resp_eur.json().get('rates', {})
        dates = sorted(list(set(data_usd.keys()) | set(data_eur.keys())))
        usd_krw = [data_usd.get(date, {}).get('KRW') for date in dates]
        eur_usd = [data_eur.get(date, {}).get('USD') for date in dates]
        return {
            'dates': dates,
            'usd_krw': usd_krw,
            'eur_usd': eur_usd
        }
    except Exception as e:
        return {'error': f'Error fetching 1-year KR FX rates: {e}'}

def get_commodity_prices_6months(fred_api_key: str, end_date: str) -> dict:
    """
    FRED API를 이용해 WTI(원유)와 금(Gold) 6개월치 일별 가격 데이터를 반환합니다.
    end_date: 'YYYY-MM-DD' (마지막 날짜)
    반환: {
        'dates': [...],
        'wti': [...],
        'gold': [...]
    }
    """
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=182)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')
        url_wti = f"https://api.stlouisfed.org/fred/series/observations?series_id=DCOILWTICO&api_key={fred_api_key}&file_type=json&observation_start={start_str}&observation_end={end_str}"
        url_gold = f"https://api.stlouisfed.org/fred/series/observations?series_id=GOLDAMGBD228NLBM&api_key={fred_api_key}&file_type=json&observation_start={start_str}&observation_end={end_str}"
        resp_wti = requests.get(url_wti)
        resp_gold = requests.get(url_gold)
        obs_wti = resp_wti.json().get('observations', [])
        obs_gold = resp_gold.json().get('observations', [])
        # 날짜 교집합만 사용
        dates = sorted(list(set([o['date'] for o in obs_wti if o['value'] not in ('.', None, '')]) & set([o['date'] for o in obs_gold if o['value'] not in ('.', None, '')])))
        wti = [float(o['value']) for o in obs_wti if o['value'] not in ('.', None, '') and o['date'] in dates]
        gold = [float(o['value']) for o in obs_gold if o['value'] not in ('.', None, '') and o['date'] in dates]
        return {
            'dates': dates,
            'wti': wti,
            'gold': gold
        }
    except Exception as e:
        return {'error': f'Error fetching 6-month commodity prices from FRED: {e}'}

def get_enhanced_stock_info(ticker: str) -> Dict:
    """
    stooq(데이터리더)로 불러올 수 있는 정보는 stooq로, 시가총액/유동주식수 등만 yfinance로 가져옵니다.
    """
    import numpy as np
    try:
        # stooq용 티커 변환
        stooq_ticker = ticker if ticker.endswith('.US') else ticker + '.US'
        # 1년치 데이터
        df_1y = web.DataReader(stooq_ticker, 'stooq', start=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'), end=datetime.now().strftime('%Y-%m-%d'))
        df_1y = df_1y.sort_index()
        # 1개월치 데이터
        df_1m = web.DataReader(stooq_ticker, 'stooq', start=(datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d'), end=datetime.now().strftime('%Y-%m-%d'))
        df_1m = df_1m.sort_index()
        # 60일치 데이터
        df_60d = web.DataReader(stooq_ticker, 'stooq', start=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'), end=datetime.now().strftime('%Y-%m-%d'))
        df_60d = df_60d.sort_index()
        if df_1y.empty or df_1m.empty or df_60d.empty:
            return {"error": f"No historical data found for {ticker} (stooq)"}
        # 현재가 (가장 최근 종가)
        current_price = df_1y['Close'].iloc[-1] if not df_1y.empty else None
        # 52주 최고가/최저가
        week_52_high = df_1y['High'].max() if not df_1y.empty else None
        week_52_low = df_1y['Low'].min() if not df_1y.empty else None
        # 60일 평균거래량
        avg_volume_60d = df_60d['Volume'].mean() if not df_60d.empty else None
        # 1개월 변동성 (표준편차 기반, 연환산)
        if len(df_1m) > 1:
            returns_1m = df_1m['Close'].pct_change().dropna()
            volatility_1m = returns_1m.std() * (252 ** 0.5) * 100
        else:
            volatility_1m = None
        # 1년 변동성 (연환산)
        if len(df_1y) > 1:
            returns_1y = df_1y['Close'].pct_change().dropna()
            volatility_1y = returns_1y.std() * (252 ** 0.5) * 100
        else:
            volatility_1y = None
        # 시가총액, 유동주식수 등은 yfinance로만 가능
        market_cap = None
        shares_outstanding = None
        float_shares = None
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 다양한 키들을 시도해보기
            market_cap = (info.get('marketCap') or 
                         info.get('market_cap') or 
                         info.get('marketCap') or
                         info.get('enterpriseValue'))
            
            shares_outstanding = (info.get('sharesOutstanding') or 
                                info.get('shares_outstanding') or
                                info.get('impliedSharesOutstanding') or
                                info.get('commonStockSharesOutstanding'))
            
            float_shares = (info.get('floatShares') or 
                           info.get('float_shares') or
                           info.get('publicFloat'))
            
            # 디버깅: 사용 가능한 키들 출력
            print(f"🔍 yfinance info keys for {ticker}: {list(info.keys())[:20]}")
            print(f"📊 market_cap: {market_cap}, shares_outstanding: {shares_outstanding}, float_shares: {float_shares}")
            
        except Exception as e:
            print(f"❌ yfinance error for {ticker}: {e}")
            market_cap = None
            shares_outstanding = None
            float_shares = None
        result = {
            "ticker": ticker,
            "current_price": round(current_price, 2) if current_price else None,
            "week_52_high": round(week_52_high, 2) if week_52_high else None,
            "week_52_low": round(week_52_low, 2) if week_52_low else None,
            "avg_volume_60d": round(avg_volume_60d, 0) if avg_volume_60d else None,
            "volatility_1m": round(volatility_1m, 2) if volatility_1m else None,
            "volatility_1y": round(volatility_1y, 2) if volatility_1y else None,
            "market_cap": market_cap,
            "shares_outstanding": shares_outstanding,
            "float_shares": float_shares
        }
        return result
    except Exception as e:
        return {"error": f"Error fetching enhanced stock info for {ticker}: {e}"}
