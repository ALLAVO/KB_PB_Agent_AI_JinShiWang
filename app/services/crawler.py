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
    개별 주식의 절대수익률과 S&P500 대비 상대수익률을 계산합니다.
    start_date, end_date: 'YYYY-MM-DD'
    반환: {
        'dates': [...],
        'stock_prices': [...],
        'sp500_prices': [...],
        'stock_index': [...],      # 기준일=100으로 정규화
        'sp500_index': [...],     # 기준일=100으로 정규화
        'relative_index': [...],   # 상대지수
        'stock_returns': [...],    # 수익률(%)
        'sp500_returns': [...],   # 수익률(%)
        'relative_returns': [...]  # 상대수익률(%)
    }
    """
    try:
        # 개별 주식 데이터 가져오기
        stock_data = get_stock_price_chart_data(ticker, start_date, end_date)
        if "error" in stock_data:
            return stock_data
        
        # S&P500 데이터 가져오기 (기존 나스닥에서 S&P500으로 변경)
        sp500_data = get_index_chart_data('^SPX', start_date, end_date)
        if "error" in sp500_data:
            return sp500_data
        
        # 날짜 매칭 (두 데이터의 교집합)
        stock_dates = set(stock_data['dates'])
        sp500_dates = set(sp500_data['dates'])
        common_dates = sorted(list(stock_dates & sp500_dates))
        
        if not common_dates:
            return {"error": "No common dates between stock and S&P500 data"}
        
        # 공통 날짜에 해당하는 데이터만 추출
        stock_prices = []
        sp500_prices = []
        
        for date in common_dates:
            stock_idx = stock_data['dates'].index(date)
            sp500_idx = sp500_data['dates'].index(date)
            stock_prices.append(stock_data['closes'][stock_idx])
            sp500_prices.append(sp500_data['closes'][sp500_idx])
        
        # 지수 계산 (기준일=100)
        stock_index = [(price / stock_prices[0]) * 100 for price in stock_prices]
        sp500_index = [(price / sp500_prices[0]) * 100 for price in sp500_prices]
        
        # 상대지수 계산
        relative_index = [(s_idx / b_idx) * 100 for s_idx, b_idx in zip(stock_index, sp500_index)]
        
        # 수익률 계산 (%)
        stock_returns = [((price / stock_prices[0]) - 1) * 100 for price in stock_prices]
        sp500_returns = [((price / sp500Prices[0]) - 1) * 100 for price in sp500_prices]
        relative_returns = [((rel_idx / 100) - 1) * 100 for rel_idx in relative_index]
        
        return {
            'dates': common_dates,
            'stock_prices': stock_prices,
            'sp500_prices': sp500_prices,
            'stock_index': stock_index,
            'sp500_index': sp500_index,
            'relative_index': relative_index,
            'stock_returns': stock_returns,
            'sp500_returns': sp500_returns,
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
        sp500_final_return = data['sp500_returns'][-1]
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
            "sp500_return": round(sp500_final_return, 2),
            "relative_return": round(relative_final_return, 2),
            "stock_volatility": round(stock_volatility, 2),
            "outperformance": round(stock_final_return - sp500_final_return, 2),
            "data_points": len(data['dates'])
        }
        
    except Exception as e:
        return {"error": f"Error generating return analysis summary: {e}"}

def get_return_analysis_table(ticker: str, start_date: str, end_date: str) -> dict:
    """
    수익률 분석 표 데이터를 반환합니다.
    절대수익률과 상대수익률을 기간별로 제공합니다.
    """
    try:
        data = calculate_absolute_and_relative_returns(ticker, start_date, end_date)
        if "error" in data:
            return data
        
        if not data['stock_returns']:
            return {"error": "No return data available"}
        
        # 최종 수익률 계산
        stock_final_return = data['stock_returns'][-1]
        sp500_final_return = data['sp500_returns'][-1]
        relative_final_return = data['relative_returns'][-1]
        
        # 1개월, 3개월, 6개월, 12개월 수익률 계산
        dates = data['dates']
        stock_returns = data['stock_returns']
        sp500_returns = data['sp500_returns']
        relative_returns = data['relative_returns']
        
        # 현재 날짜에서 역순으로 기간별 수익률 계산
        periods = {
            '1M': 22,    # 약 1개월 (22 영업일)
            '3M': 66,    # 약 3개월 (66 영업일)
            '6M': 132,   # 약 6개월 (132 영업일)
            '12M': 252   # 약 12개월 (252 영업일)
        }
        
        table_data = []
        
        for period_name, days_back in periods.items():
            if len(stock_returns) > days_back:
                # 해당 기간의 시작점과 끝점 인덱스
                start_idx = len(stock_returns) - days_back - 1
                end_idx = len(stock_returns) - 1
                
                # 기간별 수익률 계산 (시작점 대비 끝점)
                stock_start_price = data['stock_prices'][start_idx]
                stock_end_price = data['stock_prices'][end_idx]
                stock_period_return = ((stock_end_price / stock_start_price) - 1) * 100
                
                sp500_start_price = data['sp500_prices'][start_idx]
                sp500_end_price = data['sp500_prices'][end_idx]
                sp500_period_return = ((sp500_end_price / sp500_start_price) - 1) * 100
                
                # 상대수익률 = 개별주식수익률 - 벤치마크수익률
                relative_period_return = stock_period_return - sp500_period_return
                
                table_data.append({
                    'period': period_name,
                    'absolute_return': round(stock_period_return, 2),
                    'relative_return': round(relative_period_return, 2),
                    'benchmark_return': round(sp500_period_return, 2),
                    'outperformance': round(stock_period_return - sp500_period_return, 2)
                })
            else:
                # 데이터가 부족한 경우에도 기본값을 넣어서 프론트엔드에서 '-'로 표시
                table_data.append({
                    'period': period_name,
                    'absolute_return': None,
                    'relative_return': None,
                    'benchmark_return': None,
                    'outperformance': None
                })
        
        return {
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "table_data": table_data,
            "current_data": {
                "absolute_return": round(stock_final_return, 2),
                "relative_return": round(relative_final_return, 2),
                "benchmark_return": round(sp500_final_return, 2),
                "outperformance": round(stock_final_return - sp500_final_return, 2)
            }
        }
        
    except Exception as e:
        return {"error": f"Error generating return analysis table: {e}"}


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
    stooq(데이터리더)로 불러올 수 있는 정보는 stooq로, 시가총액/유동주식수 등은 Alpha Vantage로 가져옵니다.
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
        # 시가총액, 유동주식수 등은 Alpha Vantage로 가져오기
        market_cap = None
        shares_outstanding = None
        float_shares = None
        try:
            api_key = settings.ALPHAVANTAGE_API_KEY
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
            print(f"🔍 Alpha Vantage URL: {url[:50]}...{url[-20:]}")  # API 키 부분 숨기기
            resp = requests.get(url)
            print(f"📡 Alpha Vantage response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"📊 Alpha Vantage data keys: {list(data.keys())[:10]}")
                # Alpha Vantage는 데이터가 없으면 빈 dict 반환
                if data and 'Note' not in data and 'Error Message' not in data:
                    # 안전한 숫자 변환
                    def safe_int_convert(value):
                        if value and str(value).replace(',', '').replace('.', '').isdigit():
                            return int(str(value).replace(',', ''))
                        return None
                    
                    print(f"💰 Raw values - MarketCap: {data.get('MarketCapitalization')}, Shares: {data.get('SharesOutstanding')}, Float: {data.get('SharesFloat')}")
                    market_cap = safe_int_convert(data.get('MarketCapitalization'))
                    shares_outstanding = safe_int_convert(data.get('SharesOutstanding'))
                    float_shares = safe_int_convert(data.get('SharesFloat'))
                    print(f"✅ Converted values - MarketCap: {market_cap}, Shares: {shares_outstanding}, Float: {float_shares}")
                else:
                    print(f"❌ Alpha Vantage error response: {data}")
            # else: 그대로 None 유지
        except Exception as e:
            print(f"❌ Alpha Vantage error for {ticker}: {e}")
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

def get_financial_metrics_from_sec(ticker: str, end_date: str = None) -> dict:
    """
    SEC XBRL companyfacts API에서 재무지표를 추출합니다.
    - 매출액, 영업이익, 영업이익률, 순이익
    - 당해연도, 전연도 데이터
    end_date: 'YYYY-MM-DD' 형식, 이 날짜를 기준으로 연도 계산
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
        
        # 디버깅: 사용 가능한 태그들 확인
        print(f"🔍 Available US-GAAP tags for {ticker}: {list(us_gaap.keys())[:20]}...")
        
        # end_date를 기준으로 현재 연도와 전년도 계산
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                current_year = end_dt.year
            except ValueError:
                current_year = datetime.now().year
        else:
            current_year = datetime.now().year
        previous_year = current_year - 1
        
        print(f"📅 Target years: current={current_year}, previous={previous_year}")
        
        # 필요한 재무지표 태그들 (더 많은 옵션 추가)
        revenue_tags = [
            # 일반 기업용
            'Revenues', 
            'SalesRevenueNet', 
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'RevenueFromContractWithCustomerIncludingAssessedTax',
            'SalesRevenueGoodsNet',
            'SalesRevenueServicesNet',
            'RevenueFromRelatedParties',
            # 금융업용 (추가)
            'RevenuesNetOfInterestExpense',
            'BrokerageCommissionsRevenue',
            'InvestmentBankingRevenue',
            'PrincipalTransactionsRevenue'
        ]
        operating_income_tags = [
            'OperatingIncomeLoss',
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
            'IncomeLossFromContinuingOperations'
        ]
        net_income_tags = [
            'NetIncomeLoss',
            'NetIncomeLossAvailableToCommonStockholdersBasic',
            'ProfitLoss'
        ]
        
        def get_latest_value_for_year(tag_list, year):
            """특정 연도의 가장 최신 값을 가져옵니다."""
            print(f"🔍 Searching for year {year} in tags: {tag_list}")
            
            for tag in tag_list:
                if tag in us_gaap:
                    print(f"✅ Found tag: {tag}")
                    facts = us_gaap[tag].get('units', {})
                    print(f"📊 Available units for {tag}: {list(facts.keys())}")
                    
                    unit = 'USD' if 'USD' in facts else (list(facts.keys())[0] if facts else None)
                    if unit:
                        fact_list = facts[unit]
                        print(f"📈 Total facts for {tag} in {unit}: {len(fact_list)}")
                        
                        # 모든 날짜 출력 (최근 10개만)
                        all_dates = [f.get('end', 'No end date') for f in fact_list]
                        print(f"📅 Recent dates for {tag}: {sorted(all_dates, reverse=True)[:10]}")
                        
                        # 해당 연도의 데이터만 필터링
                        year_facts = [f for f in fact_list if 'end' in f and str(year) in f['end']]
                        print(f"🎯 Facts for year {year}: {len(year_facts)}")
                        
                        if year_facts:
                            # 가장 최신 날짜의 값 반환
                            latest = max(year_facts, key=lambda f: f['end'])
                            print(f"🎉 Found value for {tag} in {year}: {latest['val']} (date: {latest['end']})")
                            return latest['val']
                        else:
                            print(f"❌ No data found for {tag} in year {year}")
                else:
                    print(f"❌ Tag not found: {tag}")
            
            print(f"❌ No value found for any tag in year {year}")
            return None
        
        # 각 연도별 데이터 수집
        print(f"\n🔍 === Searching for REVENUE data ===")
        current_revenue = get_latest_value_for_year(revenue_tags, current_year)
        previous_revenue = get_latest_value_for_year(revenue_tags, previous_year)
        
        print(f"\n🔍 === Searching for OPERATING INCOME data ===")
        current_operating_income = get_latest_value_for_year(operating_income_tags, current_year)
        previous_operating_income = get_latest_value_for_year(operating_income_tags, previous_year)
        
        print(f"\n🔍 === Searching for NET INCOME data ===")
        current_net_income = get_latest_value_for_year(net_income_tags, current_year)
        previous_net_income = get_latest_value_for_year(net_income_tags, previous_year)
        
        print(f"\n📊 === FINAL RESULTS ===")
        print(f"Revenue - Current: {current_revenue}, Previous: {previous_revenue}")
        print(f"Operating Income - Current: {current_operating_income}, Previous: {previous_operating_income}")
        print(f"Net Income - Current: {current_net_income}, Previous: {previous_net_income}")
        
        # 영업이익률 계산
        current_operating_margin = None
        previous_operating_margin = None
        
        if current_revenue and current_operating_income and current_revenue != 0:
            current_operating_margin = (current_operating_income / current_revenue) * 100
            print(f"✅ Calculated current operating margin: {current_operating_margin}%")
            
        if previous_revenue and previous_operating_income and previous_revenue != 0:
            previous_operating_margin = (previous_operating_income / previous_revenue) * 100
            print(f"✅ Calculated previous operating margin: {previous_operating_margin}%")
        
        result = {
            "current_year": current_year,
            "previous_year": previous_year,
            "metrics": {
                "revenue": {
                    "current": current_revenue,
                    "previous": previous_revenue
                },
                "operating_income": {
                    "current": current_operating_income,
                    "previous": previous_operating_income
                },
                "operating_margin": {
                    "current": current_operating_margin,
                    "previous": previous_operating_margin
                },
                "net_income": {
                    "current": current_net_income,
                    "previous": previous_net_income
                }
            }
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Error fetching financial metrics: {e}"}

def get_valuation_metrics_from_sec(ticker: str, end_date: str = None) -> dict:
    """
    SEC XBRL companyfacts API에서 벨류에이션 지표를 추출합니다.
    - EPS, P/E, P/B, ROE(%)
    - 당해연도, 전연도 데이터
    end_date: 'YYYY-MM-DD' 형식, 이 날짜를 기준으로 연도 계산
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
        
        # 디버깅: 사용 가능한 태그들 확인
        print(f"🔍 Available US-GAAP tags for valuation of {ticker}: {list(us_gaap.keys())[:20]}...")
        
        # end_date를 기준으로 현재 연도와 전년도 계산
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                current_year = end_dt.year
            except ValueError:
                current_year = datetime.now().year
        else:
            current_year = datetime.now().year
        previous_year = current_year - 1
        
        print(f"📅 Valuation Target years: current={current_year}, previous={previous_year}")
        
        # 필요한 재무지표 태그들
        # EPS 관련 태그들
        eps_tags = [
            'EarningsPerShareBasic',
            'EarningsPerShareDiluted',
            'IncomeLossFromContinuingOperationsPerBasicShare',
            'IncomeLossFromContinuingOperationsPerDilutedShare'
        ]
        
        # 순이익 관련 태그들 (EPS 계산용)
        net_income_tags = [
            'NetIncomeLoss',
            'ProfitLoss',
            'IncomeLossFromContinuingOperations',
            'IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest'
        ]
        
        # 주식수 관련 태그들 (EPS 계산용) - 더 많은 태그 추가
        shares_tags = [
            'WeightedAverageNumberOfSharesOutstandingBasic',
            'WeightedAverageNumberOfDilutedSharesOutstanding',
            'CommonStockSharesOutstanding',
            'CommonStockSharesIssued',
            'SharesOutstanding',
            'NumberOfSharesOutstanding',
            'CommonStockSharesAuthorized',
            'WeightedAverageSharesOutstandingBasic',
            'WeightedAverageSharesOutstandingDiluted',
            # 분기별/연말 기준 주식수
            'CommonStockSharesOutstandingAtPeriodEnd',
            'SharesIssuedAndOutstanding'
        ]
        
        # 자기자본(Shareholders' Equity) 관련 태그들 (ROE, P/B 계산용) - 더 많은 태그 추가
        equity_tags = [
            'StockholdersEquity',
            'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 
            'StockholdersEquityAndNoncontrollingInterests',
            'PartnersCapitalIncludingPortionAttributableToNoncontrollingInterest',
            'PartnersCapital',
            'MembersEquity',
            'TotalEquity',
            'CommonStockholdersEquity',
            'ShareholdersEquityCommonStockholders',
            # 은행/금융업 특화 태그들
            'BankShareholdersEquity',
            'ShareholdersEquityBankHoldingCompany',
            # REITs 특화 태그들
            'ShareholdersEquityREIT',
            'TotalShareholdersEquity'
        ]
        
        # 주가 정보는 Stooq를 통해 조회
        try:
            # Stooq용 티커 변환
            stooq_ticker = ticker if ticker.endswith('.US') else ticker + '.US'
            
            # 2년치 데이터 가져오기 (현재년도, 전년도 커버)
            start_date = f"{previous_year}-01-01"
            end_date = f"{current_year}-12-31"
            
            print(f"📈 Fetching stock data from Stooq for {stooq_ticker}: {start_date} to {end_date}")
            df = web.DataReader(stooq_ticker, 'stooq', start=start_date, end=end_date)
            
            if not df.empty:
                df = df.sort_index()
                print(f"📊 Stock data range: {df.index[0]} to {df.index[-1]} ({len(df)} records)")
                
                # 현재 주가 (가장 최근)
                current_price = df['Close'].iloc[-1]
                print(f"💰 Current price: {current_price}")
                
                # 전년도 말 주가 (12월 말 또는 가장 가까운 날짜)
                previous_year_data = df[df.index.year == previous_year]
                if not previous_year_data.empty:
                    previous_price = previous_year_data['Close'].iloc[-1]  # 전년도 마지막 거래일
                    print(f"💰 Previous year price: {previous_price} (date: {previous_year_data.index[-1]})")
                else:
                    previous_price = None
                    print(f"❌ No stock data found for previous year {previous_year}")
                
                # 주식수는 yfinance에서만 가져올 수 있음 (Stooq에는 없음)
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    shares_outstanding = info.get('sharesOutstanding')
                    print(f"📈 Shares outstanding: {shares_outstanding}")
                except:
                    shares_outstanding = None
                    print(f"❌ Could not fetch shares outstanding from yfinance")
            else:
                print(f"❌ No stock data found for {stooq_ticker}")
                current_price = None
                previous_price = None
                shares_outstanding = None
                
        except Exception as e:
            print(f"⚠️ Error fetching stock data from Stooq: {e}")
            current_price = None
            previous_price = None
            shares_outstanding = None
        
        def find_metric_value(tags, target_year, metric_name="Unknown"):
            """주어진 태그들에서 특정 연도의 값을 찾는 함수 (개선된 디버깅 포함)"""
            print(f"\n🔍 === Searching for {metric_name} in year {target_year} ===")
            
            for tag in tags:
                if tag in us_gaap:
                    print(f"✅ Found tag: {tag}")
                    tag_data = us_gaap[tag]
                    units = tag_data.get('units', {})
                    print(f"📊 Available units for {tag}: {list(units.keys())}")
                    
                    for unit_type, unit_data in units.items():
                        print(f"📈 Checking unit: {unit_type} ({len(unit_data)} entries)")
                        
                        # 해당 연도의 모든 데이터 찾기 (더 유연한 검색)
                        year_entries = []
                        for entry in unit_data:
                            entry_year = entry.get('fy')
                            entry_form = entry.get('form', 'Unknown')
                            entry_end = entry.get('end', 'No date')
                            entry_val = entry.get('val')
                            entry_period = entry.get('fp', 'Unknown')  # FY=Annual, Q1,Q2,Q3,Q4=Quarterly
                            
                            # 해당 연도의 데이터만 수집 (연간 데이터 우선, 분기 데이터도 고려)
                            if entry_year == target_year:
                                year_entries.append({
                                    'year': entry_year,
                                    'form': entry_form,
                                    'end': entry_end,
                                    'val': entry_val,
                                    'period': entry_period
                                })
                        
                        print(f"🎯 Found {len(year_entries)} entries for year {target_year}")
                        for entry in year_entries:
                            print(f"   - Form: {entry['form']}, Period: {entry['period']}, End: {entry['end']}, Value: {entry['val']}")
                        
                        # 우선순위: Annual(FY) > Q4 > Q3 > Q2 > Q1, 10-K > 10-Q, 최신 날짜 우선
                        if year_entries:
                            # 1순위: Annual 데이터 중 10-K
                            annual_k = [e for e in year_entries if e['period'] == 'FY' and e['form'] == '10-K']
                            if annual_k:
                                selected = max(annual_k, key=lambda x: x['end'])
                                print(f"🎉 Selected Annual 10-K entry: {selected}")
                                return selected['val']
                            
                            # 2순위: Annual 데이터 중 기타
                            annual_other = [e for e in year_entries if e['period'] == 'FY']
                            if annual_other:
                                selected = max(annual_other, key=lambda x: x['end'])
                                print(f"🎉 Selected Annual entry: {selected}")
                                return selected['val']
                            
                            # 3순위: Q4 데이터 (연말과 가장 가까움)
                            q4_data = [e for e in year_entries if e['period'] == 'Q4']
                            if q4_data:
                                selected = max(q4_data, key=lambda x: x['end'])
                                print(f"🎉 Selected Q4 entry: {selected}")
                                return selected['val']
                            
                            # 4순위: 10-K 폼 (기간 상관없이)
                            k_forms = [e for e in year_entries if e['form'] == '10-K']
                            if k_forms:
                                selected = max(k_forms, key=lambda x: x['end'])
                                print(f"🎉 Selected 10-K entry: {selected}")
                                return selected['val']
                            
                            # 5순위: 10-Q 폼 중 최신
                            q_forms = [e for e in year_entries if e['form'] == '10-Q']
                            if q_forms:
                                selected = max(q_forms, key=lambda x: x['end'])
                                print(f"🎉 Selected 10-Q entry: {selected}")
                                return selected['val']
                            
                            # 6순위: 기타 폼 중 최신
                            selected = max(year_entries, key=lambda x: x['end'])
                            print(f"🎉 Selected other form entry: {selected}")
                            return selected['val']
                else:
                    print(f"❌ Tag not found: {tag}")
            
            print(f"❌ No value found for {metric_name} in year {target_year}")
            return None
        
        # 각 지표별 현재년도, 전년도 값 추출
        current_eps = find_metric_value(eps_tags, current_year, "EPS")
        previous_eps = find_metric_value(eps_tags, previous_year, "EPS")
        
        current_net_income = find_metric_value(net_income_tags, current_year, "Net Income")
        previous_net_income = find_metric_value(net_income_tags, previous_year, "Net Income")
        
        current_shares = find_metric_value(shares_tags, current_year, "Shares Outstanding")
        previous_shares = find_metric_value(shares_tags, previous_year, "Shares Outstanding")
        
        current_equity = find_metric_value(equity_tags, current_year, "Shareholders Equity")
        previous_equity = find_metric_value(equity_tags, previous_year, "Shareholders Equity")
        
        print(f"\n📊 === RAW DATA SUMMARY ===")
        print(f"EPS - Current: {current_eps}, Previous: {previous_eps}")
        print(f"Net Income - Current: {current_net_income}, Previous: {previous_net_income}")
        print(f"Shares - Current: {current_shares}, Previous: {previous_shares}")
        print(f"Equity - Current: {current_equity}, Previous: {previous_equity}")
        print(f"Stock Price - Current: {current_price}, Previous: {previous_price}")
        print(f"Shares Outstanding (yf): {shares_outstanding}")
        
        # EPS 계산 (직접 값이 없는 경우)
        if current_eps is None and current_net_income and current_shares:
            current_eps = current_net_income / current_shares
            print(f"✅ Calculated current EPS: {current_eps}")
        if previous_eps is None and previous_net_income and previous_shares:
            previous_eps = previous_net_income / previous_shares
            print(f"✅ Calculated previous EPS: {previous_eps}")
        
        # P/E 계산
        current_pe = None
        previous_pe = None
        if current_eps and current_eps > 0 and current_price:
            current_pe = current_price / current_eps
            print(f"✅ Calculated current P/E: {current_pe} (Price: {current_price} / EPS: {current_eps})")
        else:
            print(f"❌ Cannot calculate current P/E - EPS: {current_eps}, Price: {current_price}")
            
        if previous_eps and previous_eps > 0 and previous_price:
            previous_pe = previous_price / previous_eps
            print(f"✅ Calculated previous P/E: {previous_pe} (Price: {previous_price} / EPS: {previous_eps})")
        else:
            print(f"❌ Cannot calculate previous P/E - EPS: {previous_eps}, Price: {previous_price}")
        
        # P/B 계산 (Book Value per Share = Equity / Shares Outstanding)
        current_pb = None
        previous_pb = None
        
        # 현재년도 P/B 계산
        if current_equity and shares_outstanding and current_price:
            book_value_per_share = current_equity / shares_outstanding
            if book_value_per_share > 0:
                current_pb = current_price / book_value_per_share
                print(f"✅ Calculated current P/B: {current_pb} (Price: {current_price} / BVPS: {book_value_per_share})")
            else:
                print(f"❌ Current BVPS is not positive: {book_value_per_share}")
        else:
            print(f"❌ Cannot calculate current P/B - Equity: {current_equity}, Shares: {shares_outstanding}, Price: {current_price}")
        
        # 전년도 P/B 계산 - 전년도 자기자본과 전년도 말 주식수 사용
        if previous_equity and previous_price:
            # 전년도 주식수가 있으면 사용, 없으면 현재 주식수 사용 (일반적으로 큰 변화 없음)
            shares_for_previous = previous_shares if previous_shares else shares_outstanding
            
            if shares_for_previous:
                previous_book_value_per_share = previous_equity / shares_for_previous
                if previous_book_value_per_share > 0:
                    previous_pb = previous_price / previous_book_value_per_share
                    print(f"✅ Calculated previous P/B: {previous_pb} (Price: {previous_price} / BVPS: {previous_book_value_per_share})")
                    print(f"   📊 Used shares: {shares_for_previous} ({'from SEC' if previous_shares else 'from yfinance (current)'})")
                else:
                    print(f"❌ Previous BVPS is not positive: {previous_book_value_per_share}")
            else:
                print(f"❌ No shares data available for previous P/B calculation")
        else:
            print(f"❌ Cannot calculate previous P/B - Equity: {previous_equity}, Price: {previous_price}")
            
        # P/B 계산에 대한 추가 디버깅 정보
        print(f"\n🔍 === P/B CALCULATION DEBUG ===")
        print(f"Current Equity: {current_equity:,}" if current_equity else f"Current Equity: {current_equity}")
        print(f"Previous Equity: {previous_equity:,}" if previous_equity else f"Previous Equity: {previous_equity}")
        print(f"Current Shares (SEC): {current_shares:,}" if current_shares else f"Current Shares (SEC): {current_shares}")
        print(f"Previous Shares (SEC): {previous_shares:,}" if previous_shares else f"Previous Shares (SEC): {previous_shares}")
        print(f"Shares Outstanding (yf): {shares_outstanding:,}" if shares_outstanding else f"Shares Outstanding (yf): {shares_outstanding}")
        print(f"Current Price: ${current_price}" if current_price else f"Current Price: {current_price}")
        print(f"Previous Price: ${previous_price}" if previous_price else f"Previous Price: {previous_price}")
        
        # ROE 계산 (Return on Equity = Net Income / Shareholders' Equity * 100)
        current_roe = None
        previous_roe = None
        if current_net_income and current_equity and current_equity > 0:
            current_roe = (current_net_income / current_equity) * 100
            print(f"✅ Calculated current ROE: {current_roe}% (NI: {current_net_income} / Equity: {current_equity})")
        else:
            print(f"❌ Cannot calculate current ROE - Net Income: {current_net_income}, Equity: {current_equity}")
            
        if previous_net_income and previous_equity and previous_equity > 0:
            previous_roe = (previous_net_income / previous_equity) * 100
            print(f"✅ Calculated previous ROE: {previous_roe}% (NI: {previous_net_income} / Equity: {previous_equity})")
        else:
            print(f"❌ Cannot calculate previous ROE - Net Income: {previous_net_income}, Equity: {previous_equity}")
        
        # 값 정리 (소수점 2자리)
        def format_value(value):
            if value is None:
                return None
            return round(float(value), 2)
        
        result = {
            "ticker": ticker,
            "current_year": current_year,
            "previous_year": previous_year,
            "metrics": {
                "eps": {
                    "current": format_value(current_eps),
                    "previous": format_value(previous_eps)
                },
                "pe_ratio": {
                    "current": format_value(current_pe),
                    "previous": format_value(previous_pe)
                },
                "pb_ratio": {
                    "current": format_value(current_pb),
                    "previous": format_value(previous_pb)
                },
                "roe_percent": {
                    "current": format_value(current_roe),
                    "previous": format_value(previous_roe)
                }
            },
            "raw_data": {
                "current_price": format_value(current_price),
                "previous_price": format_value(previous_price),
                "shares_outstanding_yf": shares_outstanding,
                "current_net_income": format_value(current_net_income),
                "previous_net_income": format_value(previous_net_income),
                "current_equity": format_value(current_equity),
                "previous_equity": format_value(previous_equity),
                "current_shares_sec": format_value(current_shares),
                "previous_shares_sec": format_value(previous_shares),
                # P/B 계산을 위한 추가 정보
                "current_book_value_per_share": format_value(current_equity / shares_outstanding) if current_equity and shares_outstanding else None,
                "previous_book_value_per_share": format_value(previous_equity / (previous_shares or shares_outstanding)) if previous_equity and (previous_shares or shares_outstanding) else None
            }
        }
        
        print(f"\n🎯 === FINAL VALUATION METRICS RESULT ===")
        print(f"Ticker: {ticker}")
        print(f"Years: {current_year} (current) / {previous_year} (previous)")
        print(f"EPS: {result['metrics']['eps']['current']} / {result['metrics']['eps']['previous']}")
        print(f"P/E: {result['metrics']['pe_ratio']['current']} / {result['metrics']['pe_ratio']['previous']}")
        print(f"P/B: {result['metrics']['pb_ratio']['current']} / {result['metrics']['pb_ratio']['previous']}")
        print(f"ROE: {result['metrics']['roe_percent']['current']}% / {result['metrics']['roe_percent']['previous']}%")
        
        return result
        
    except Exception as e:
        return {"error": f"Error fetching valuation metrics: {e}"}
