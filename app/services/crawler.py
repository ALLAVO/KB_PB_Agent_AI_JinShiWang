import requests
import time
import os
import json
import pandas_datareader.data as web
from app.core.config import settings
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from openai import OpenAI
from app.db.connection import check_db_connection
import numpy as np

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
def get_company_profile_from_fmp(ticker: str) -> dict:
    """
    Financial Modeling Prep API를 통해 기업의 name, sector, industry, description, address를 반환합니다.
    """
    try:
        api_key = settings.FMP_API_KEY
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
        print(f"🔍 FMP URL for {ticker}: {url[:50]}...{url[-20:]}")  # API 키 부분 숨기기
        resp = requests.get(url)
        print(f"📡 FMP response status for {ticker}: {resp.status_code}")
        
        if resp.status_code != 200:
            return {"error": f"FMP API request failed: {resp.status_code}"}
        
        data = resp.json()
        print(f"📊 FMP raw response for {ticker}: {data}")
        
        # FMP는 배열로 반환하므로 첫 번째 항목 사용
        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"❌ FMP error or empty response for {ticker}: {data}")
            return {"error": f"No company profile data found for {ticker}"}
        
        info = data[0]  # 첫 번째 회사 정보
        
        # API 에러 메시지 확인
        if 'Error Message' in info:
            print(f"⚠️ FMP API error for {ticker}: {info['Error Message']}")
            return {"error": f"FMP API error: {info['Error Message']}"}
        
        # 원본 설명 가져오기
        original_description = info.get("description", "")
        company_name = info.get("companyName", ticker)
        
        # OpenAI로 설명 요약
        summarized_description = summarize_company_description_with_openai(original_description, company_name)
        
        result = {
            "company_name": company_name,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "address": f"{info.get('address', '')}, {info.get('city', '')}, {info.get('state', '')}, {info.get('country', '')}".strip(', '),
            "description": summarized_description
        }
        print(f"✅ FMP parsed result for {ticker}: {result}")
        return result
    except Exception as e:
        print(f"❌ Exception in FMP request for {ticker}: {e}")
        return {"error": f"Error fetching company profile from FMP: {e}"}


def summarize_company_description_with_openai(description: str, company_name: str = "") -> str:
    """
    OpenAI API를 사용해서 회사 설명을 2-3줄 이내 한국어로 요약합니다.
    """
    if not description or description.strip() == "":
        return "회사 설명이 제공되지 않았습니다."
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""
다음은 {company_name} 회사의 영문 설명입니다. 이를 2-3줄 이내의 한국어로 간단명료하게 요약해주세요.
핵심 사업영역과 주요 제품/서비스만 포함하여 최대한 간결하게 작성해주세요.

회사 설명:
{description}

요약 (2-3줄 이내):
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"✅ OpenAI summary for {company_name}: {summary}")
        return summary
        
    except Exception as e:
        print(f"❌ OpenAI summarization error for {company_name}: {e}")
        # 실패시 원본 설명의 첫 100자만 반환
        return description[:100] + "..." if len(description) > 100 else description


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
        sp500_returns = [((price / sp500_prices[0]) - 1) * 100 for price in sp500_prices]
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
    DOW, S&P500, NASDAQ 6개월치 일별 종가 데이터를 데이터베이스에서 반환합니다.
    end_date: 'YYYY-MM-DD' (그래프 마지막 날짜)
    반환: {
        'dow': {'dates': [...], 'closes': [...]},
        'sp500': {'dates': [...], 'closes': [...]},
        'nasdaq': {'dates': [...], 'closes': [...]}
    }
    """
    conn = check_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}
    
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=182)  # 약 6개월(182일)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')

        cur = conn.cursor()
        query = """
            SELECT date, dow, sp500, nasdaq 
            FROM index_closing_price 
            WHERE date BETWEEN %s AND %s
            ORDER BY date ASC;
        """
        cur.execute(query, (start_str, end_str))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # 데이터 구조화
        dates = []
        dow_closes = []
        sp500_closes = []
        nasdaq_closes = []
        
        for row in rows:
            # row[0]이 이미 문자열인 경우와 datetime 객체인 경우를 모두 처리
            if isinstance(row[0], str):
                dates.append(row[0])
            else:
                dates.append(row[0].strftime('%Y-%m-%d'))
            dow_closes.append(float(row[1]) if row[1] is not None else None)
            sp500_closes.append(float(row[2]) if row[2] is not None else None)
            nasdaq_closes.append(float(row[3]) if row[3] is not None else None)
        
        result = {
            'dow': {'dates': dates, 'closes': dow_closes},
            'sp500': {'dates': dates, 'closes': sp500_closes},
            'nasdaq': {'dates': dates, 'closes': nasdaq_closes}
        }
        
        return result
        
    except Exception as e:
        if conn:
            conn.close()
        return {'error': f'Error fetching 6-month US indices data from database: {e}'}

def get_us_indices_1year_chart(end_date: str) -> dict:
    """
    DOW, S&P500, NASDAQ 1년치 일별 종가 데이터를 데이터베이스에서 반환합니다.
    end_date: 'YYYY-MM-DD' (그래프 마지막 날짜)
    반환: {
        'dow': {'dates': [...], 'closes': [...]},
        'sp500': {'dates': [...], 'closes': [...]},
        'nasdaq': {'dates': [...], 'closes': [...]}
    }
    """
    conn = check_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}
    
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=365)  # 1년(365일)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')

        cur = conn.cursor()
        query = """
            SELECT date, dow, sp500, nasdaq 
            FROM index_closing_price 
            WHERE date BETWEEN %s AND %s
            ORDER BY date ASC;
        """
        cur.execute(query, (start_str, end_str))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # 데이터 구조화
        dates = []
        dow_closes = []
        sp500_closes = []
        nasdaq_closes = []
        
        for row in rows:
            # row[0]이 이미 문자열인 경우와 datetime 객체인 경우를 모두 처리
            if isinstance(row[0], str):
                dates.append(row[0])
            else:
                dates.append(row[0].strftime('%Y-%m-%d'))
            dow_closes.append(float(row[1]) if row[1] is not None else None)
            sp500_closes.append(float(row[2]) if row[2] is not None else None)
            nasdaq_closes.append(float(row[3]) if row[3] is not None else None)
        
        result = {
            'dow': {'dates': dates, 'closes': dow_closes},
            'sp500': {'dates': dates, 'closes': sp500_closes},
            'nasdaq': {'dates': dates, 'closes': nasdaq_closes}
        }
        
        return result
        
    except Exception as e:
        if conn:
            conn.close()
        return {'error': f'Error fetching 1-year US indices data from database: {e}'}

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
    주가 관련 정보는 DB에서, 시가총액/유동주식수 등은 FMP API로 가져옵니다.
    """
    try:
        # DB 테이블 선택
        first_char = ticker[0].lower()
        if 'a' <= first_char <= 'd':
            table_name = 'fnspid_stock_price_a'
        elif 'e' <= first_char <= 'm':
            table_name = 'fnspid_stock_price_b'
        else:
            table_name = 'fnspid_stock_price_c'

        conn = check_db_connection()
        if conn is None:
            return {"error": "Database connection failed"}
        cur = conn.cursor()
        now = datetime.now()
        date_1y_ago = (now - timedelta(days=365)).strftime('%Y-%m-%d')
        date_1m_ago = (now - timedelta(days=31)).strftime('%Y-%m-%d')
        date_60d_ago = (now - timedelta(days=60)).strftime('%Y-%m-%d')
        now_str = now.strftime('%Y-%m-%d')

        # 1년치 데이터
        cur.execute(f"""
            SELECT date, high, low, close, volume
            FROM {table_name}
            WHERE stock_symbol = %s AND date BETWEEN %s AND %s
            ORDER BY date ASC
        """, (ticker, date_1y_ago, now_str))
        rows_1y = cur.fetchall()
        # 1개월치 데이터
        cur.execute(f"""
            SELECT date, close
            FROM {table_name}
            WHERE stock_symbol = %s AND date BETWEEN %s AND %s
            ORDER BY date ASC
        """, (ticker, date_1m_ago, now_str))
        rows_1m = cur.fetchall()
        # 60일치 데이터
        cur.execute(f"""
            SELECT date, volume
            FROM {table_name}
            WHERE stock_symbol = %s AND date BETWEEN %s AND %s
            ORDER BY date ASC
        """, (ticker, date_60d_ago, now_str))
        rows_60d = cur.fetchall()
        cur.close()
        conn.close()

        if not rows_1y or not rows_1m or not rows_60d:
            return {"error": f"No historical data found for {ticker} (DB)"}

        # 1년치 데이터 처리
        highs_1y = [float(r[1]) for r in rows_1y if r[1] is not None]
        lows_1y = [float(r[2]) for r in rows_1y if r[2] is not None]
        closes_1y = [float(r[3]) for r in rows_1y if r[3] is not None]
        # 현재가 (가장 최근 종가)
        current_price = closes_1y[-1] if closes_1y else None
        # 52주 최고가/최저가
        week_52_high = max(highs_1y) if highs_1y else None
        week_52_low = min(lows_1y) if lows_1y else None
        # 1년 변동성 (연환산)
        if len(closes_1y) > 1:
            returns_1y = [(closes_1y[i] / closes_1y[i-1] - 1) for i in range(1, len(closes_1y))]
            volatility_1y = np.std(returns_1y) * (252 ** 0.5) * 100
        else:
            volatility_1y = None
        # 1개월 변동성 (연환산)
        closes_1m = [float(r[1]) for r in rows_1m if r[1] is not None]
        if len(closes_1m) > 1:
            returns_1m = [(closes_1m[i] / closes_1m[i-1] - 1) for i in range(1, len(closes_1m))]
            volatility_1m = np.std(returns_1m) * (252 ** 0.5) * 100
        else:
            volatility_1m = None
        # 60일 평균거래량
        volumes_60d = [float(r[1]) for r in rows_60d if r[1] is not None]
        avg_volume_60d = np.mean(volumes_60d) if volumes_60d else None

        # FMP API로 시가총액 등 정보
        market_cap = None
        shares_outstanding = None
        float_shares = None
        try:
            api_key = settings.FMP_API_KEY
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0:
                    company_data = data[0]
                    def safe_int_convert(value):
                        if value is None:
                            return None
                        try:
                            return int(float(str(value).replace(',', '')))
                        except (ValueError, TypeError):
                            return None
                    market_cap = safe_int_convert(company_data.get('mktCap'))
                    shares_outstanding = safe_int_convert(company_data.get('sharesOutstanding'))
                    float_shares = shares_outstanding
        except Exception as e:
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


def get_financial_metrics_from_fmp(ticker: str) -> dict:
    """
    FMP API의 Income Statement를 통해 재무지표를 가져옵니다.
    - 매출액, 영업이익, 영업이익률, 순이익
    - 최근 2년치 데이터 제공
    """
    try:
        api_key = settings.FMP_API_KEY
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=2&apikey={api_key}"
        print(f"� FMP Income Statement URL for {ticker}: {url[:50]}...{url[-20:]}")
        
        resp = requests.get(url)
        print(f"📡 FMP Income Statement response status for {ticker}: {resp.status_code}")
        
        if resp.status_code != 200:
            return {"error": f"FMP Income Statement API request failed: {resp.status_code}"}
        
        data = resp.json()
        print(f"📊 FMP Income Statement data for {ticker}: {len(data)} entries found")
        
        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"❌ FMP Income Statement: No data found for {ticker}")
            return {"error": f"No income statement data found for {ticker}"}
        
        # 최근 2년 데이터 추출
        current_data = data[0] if len(data) > 0 else None
        previous_data = data[1] if len(data) > 1 else None
        
        def safe_float(value):
            """안전한 float 변환"""
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_percentage(numerator, denominator):
            """안전한 퍼센트 계산"""
            if numerator is None or denominator is None or denominator == 0:
                return None
            try:
                return round((float(numerator) / float(denominator)) * 100, 2)
            except (ValueError, TypeError, ZeroDivisionError):
                return None
        
        # 현재년도 데이터
        current_revenue = safe_float(current_data.get("revenue")) if current_data else None
        current_operating_income = safe_float(current_data.get("operatingIncome")) if current_data else None
        current_net_income = safe_float(current_data.get("netIncome")) if current_data else None
        
        # 전년도 데이터
        previous_revenue = safe_float(previous_data.get("revenue")) if previous_data else None
        previous_operating_income = safe_float(previous_data.get("operatingIncome")) if previous_data else None
        previous_net_income = safe_float(previous_data.get("netIncome")) if previous_data else None
        
        # 영업이익률 계산
        current_operating_margin = safe_percentage(current_operating_income, current_revenue)
        previous_operating_margin = safe_percentage(previous_operating_income, previous_revenue)
        
        result = {
            "ticker": ticker,
            "current_year": current_data.get("calendarYear") if current_data else None,
            "previous_year": previous_data.get("calendarYear") if previous_data else None,
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
        
        print(f"✅ FMP Income Statement result for {ticker}:")
        print(f"   Revenue: {current_revenue} / {previous_revenue}")
        print(f"   Operating Income: {current_operating_income} / {previous_operating_income}")
        print(f"   Operating Margin: {current_operating_margin}% / {previous_operating_margin}%")
        print(f"   Net Income: {current_net_income} / {previous_net_income}")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception in FMP Income Statement request for {ticker}: {e}")
        return {"error": f"Error fetching financial metrics from FMP: {e}"}

def get_valuation_metrics_from_sec(ticker: str, end_date: str = None) -> dict:
    """
    FMP API를 통해 벨류에이션 지표를 가져옵니다.
    - P/E Ratio, P/B Ratio, ROE 등
    - 최근 5년치 데이터 제공
    
    Note: This function has been replaced with FMP API for better reliability.
    The end_date parameter is kept for compatibility but not used.
    """
    return get_valuation_metrics_from_fmp(ticker)

def get_valuation_metrics_from_fmp(ticker: str) -> dict:
    """
    FMP API를 통해 벨류에이션 지표를 가져옵니다.
    - P/E Ratio, P/B Ratio, ROE 등
    - 최근 5년치 데이터 제공
    """
    try:
        api_key = settings.FMP_API_KEY
        url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={api_key}"
        print(f"🔍 FMP Ratios URL for {ticker}: {url[:50]}...{url[-20:]}")
        
        resp = requests.get(url)
        print(f"📡 FMP Ratios response status for {ticker}: {resp.status_code}")
        
        if resp.status_code != 200:
            return {"error": f"FMP Ratios API request failed: {resp.status_code}"}
        
        data = resp.json()
        print(f"📊 FMP Ratios data for {ticker}: {len(data)} entries found")
        
        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"❌ FMP Ratios: No data found for {ticker}")
            return {"error": f"No ratios data found for {ticker}"}
        
        # 최근 2년 데이터 추출 (현재년도, 전년도)
        current_data = data[0] if len(data) > 0 else None
        previous_data = data[1] if len(data) > 1 else None
        
        def safe_float(value):
            """안전한 float 변환"""
            if value is None or value == "":
                return None
            try:
                return round(float(value), 2)
            except (ValueError, TypeError):
                return None
        
        # EPS 데이터를 Income Statement API에서 가져오기
        current_eps = None
        previous_eps = None
        try:
            income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=2&apikey={api_key}"
            income_resp = requests.get(income_url)
            if income_resp.status_code == 200:
                income_data = income_resp.json()
                if income_data and isinstance(income_data, list):
                    current_eps = safe_float(income_data[0].get("eps")) if len(income_data) > 0 else None
                    previous_eps = safe_float(income_data[1].get("eps")) if len(income_data) > 1 else None
                    print(f"📈 EPS from Income Statement - Current: {current_eps}, Previous: {previous_eps}")
        except Exception as e:
            print(f"⚠️ Could not fetch EPS from Income Statement: {e}")
        
        result = {
            "ticker": ticker,
            "current_year": current_data.get("calendarYear") if current_data else None,
            "previous_year": previous_data.get("calendarYear") if previous_data else None,
            "metrics": {
                "eps": {
                    "current": current_eps,
                    "previous": previous_eps
                },
                "pe_ratio": {
                    "current": safe_float(current_data.get("priceEarningsRatio")) if current_data else None,
                    "previous": safe_float(previous_data.get("priceEarningsRatio")) if previous_data else None
                },
                "pb_ratio": {
                    "current": safe_float(current_data.get("priceToBookRatio")) if current_data else None,
                    "previous": safe_float(previous_data.get("priceToBookRatio")) if previous_data else None
                },
                "roe_percent": {
                    "current": safe_float(current_data.get("returnOnEquity")) if current_data else None,
                    "previous": safe_float(previous_data.get("returnOnEquity")) if previous_data else None
                }
            },
            "additional_ratios": {
                "current_ratio": safe_float(current_data.get("currentRatio")) if current_data else None,
                "quick_ratio": safe_float(current_data.get("quickRatio")) if current_data else None,
                "debt_to_equity": safe_float(current_data.get("debtEquityRatio")) if current_data else None,
                "gross_profit_margin": safe_float(current_data.get("grossProfitMargin")) if current_data else None,
                "operating_profit_margin": safe_float(current_data.get("operatingProfitMargin")) if current_data else None,
                "net_profit_margin": safe_float(current_data.get("netProfitMargin")) if current_data else None
            }
        }
        
        print(f"✅ FMP Ratios result for {ticker}:")
        print(f"   EPS: {result['metrics']['eps']['current']} / {result['metrics']['eps']['previous']}")
        print(f"   P/E: {result['metrics']['pe_ratio']['current']} / {result['metrics']['pe_ratio']['previous']}")
        print(f"   P/B: {result['metrics']['pb_ratio']['current']} / {result['metrics']['pb_ratio']['previous']}")
        print(f"   ROE: {result['metrics']['roe_percent']['current']}% / {result['metrics']['roe_percent']['previous']}%")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception in FMP Ratios request for {ticker}: {e}")
        return {"error": f"Error fetching ratios from FMP: {e}"}
