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
from app.db.connection import get_sqlalchemy_engine
from sqlalchemy import text 


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

# 데이터베이스에서 주간 주가(종가, 시가, 고가, 저가, 거래량)와 기술지표(주간 변동성 등)를 반환하는 함수
def get_weekly_stock_indicators_from_stooq(ticker: str, start_date: str, end_date: str) -> dict:
    """
    데이터베이스에서 주간 주가(종가, 시가, 고가, 저가, 거래량)와 기술지표(주간 변동성 등)를 반환합니다.
    start_date, end_date: 'YYYY-MM-DD' (주차의 시작일, 마지막날)
    반환: {
        'close_avg', 'open_avg', 'high_avg', 'low_avg', 'volume_avg',
        'volatility', 'price_change_pct'
    }
    """
    try:
        # 티커 첫 글자에 따라 테이블 결정
        first_letter = ticker[0].lower()
        if 'a' <= first_letter <= 'd':
            table_name = 'fnspid_stock_price_a'
        elif 'e' <= first_letter <= 'm':
            table_name = 'fnspid_stock_price_b'
        elif 'n' <= first_letter <= 'z':
            table_name = 'fnspid_stock_price_c'
        else:
            return {"error": f"Invalid ticker format: {ticker}"}
        
        # 2023년까지의 데이터만 있으므로 end_date가 2023년을 넘으면 조정
        if end_date > '2023-12-31':
            end_date = '2023-12-31'
        if start_date > '2023-12-31':
            return {"error": "No data available for the requested period (data only until 2023)"}
        
        with get_sqlalchemy_engine().connect() as conn:
            # 주간 데이터 조회 (SQLAlchemy 2.x 호환되도록 수정)
            query = text(f"""
                SELECT date, open, high, low, close, volume, adj_close
                FROM {table_name}
                WHERE stock_symbol = :ticker AND date BETWEEN :start_date AND :end_date
                ORDER BY date ASC
            """)
            params = {"ticker": ticker, "start_date": start_date, "end_date": end_date}
            result = conn.execute(query, params)
            rows = result.mappings().all()
        
        if not rows:
            return {"error": "No price data in given period."}
        
        # DataFrame 생성 (딕셔너리 리스트를 사용하므로 columns 인자 불필요)
        df = pd.DataFrame(rows)
        
        # 날짜를 인덱스로 설정하고 정렬
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        # 통계 계산 (adj_close 사용)
        close_avg = df['adj_close'].mean()
        open_avg = df['open'].mean()
        high_avg = df['high'].mean()
        low_avg = df['low'].mean()
        volume_avg = df['volume'].mean()
        volatility = df['adj_close'].std()
        price_change_pct = ((df['adj_close'].iloc[-1] - df['adj_close'].iloc[0]) / df['adj_close'].iloc[0]) * 100 if len(df['adj_close']) > 1 else None
        
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
        return {"error": f"Error fetching stock indicators from database: {e}"}

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
    주식 가격 차트 데이터를 데이터베이스에서 가져옵니다.
    """
    try:
        # 티커 첫 글자에 따라 테이블 결정
        first_letter = ticker[0].lower()
        if 'a' <= first_letter <= 'd':
            table_name = 'fnspid_stock_price_a'
        elif 'e' <= first_letter <= 'm':
            table_name = 'fnspid_stock_price_b'
        elif 'n' <= first_letter <= 'z':
            table_name = 'fnspid_stock_price_c'
        else:
            return {"error": f"Invalid ticker format: {ticker}"}
        
        # 2023년까지의 데이터만 있으므로 end_date가 2023년을 넘으면 조정
        if end_date > '2023-12-31':
            end_date = '2023-12-31'
        if start_date > '2023-12-31':
            return {"error": "No data available for the requested period (data only until 2023)"}
        
        with get_sqlalchemy_engine().connect() as conn:
            # 차트 데이터 조회 (SQLAlchemy 2.x 호환되도록 수정)
            query = text(f"""
                SELECT date, open, high, low, close, volume, adj_close
                FROM {table_name}
                WHERE stock_symbol = :ticker AND date BETWEEN :start_date AND :end_date
                ORDER BY date ASC
            """)
            params = {"ticker": ticker, "start_date": start_date, "end_date": end_date}
            result = conn.execute(query, params)
            rows = result.mappings().all()  # 수정된 부분
        
        if not rows:
            return {"error": f"No data found for symbol {ticker}"}
        
        # 데이터 구조화 (딕셔너리 접근 방식으로 변경)
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for row in rows:
            # row는 이제 딕셔너리 형태
            if isinstance(row['date'], str):
                dates.append(row['date'])
            else:
                dates.append(row['date'].strftime('%Y-%m-%d'))
            opens.append(float(row['open']) if row['open'] is not None else None)
            highs.append(float(row['high']) if row['high'] is not None else None)
            lows.append(float(row['low']) if row['low'] is not None else None)
            closes.append(float(row['close']) if row['close'] is not None else None)
            volumes.append(float(row['volume']) if row['volume'] is not None else None)
        
        return {
            "dates": dates,
            "closes": closes,
            "opens": opens,
            "highs": highs,
            "lows": lows,
            "volumes": volumes
        }
    except Exception as e:
        return {"error": f"Error fetching stock data from database for {ticker}: {e}"}

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
    지수 데이터를 데이터베이스에서 가져옵니다 (나스닥, S&P 500, DOW 등)
    """
    try:
        # 2023년까지의 데이터만 있으므로 end_date가 2023년을 넘으면 조정
        if end_date > '2023-12-31':
            end_date = '2023-12-31'
        if start_date > '2023-12-31':
            return {"error": "No data available for the requested period (data only until 2023)"}
        
        # 심볼에 따라 컬럼명 매핑
        symbol_mapping = {
            '^SPX': 'sp500',
            '^IXIC': 'nasdaq', 
            '^NDQ': 'nasdaq',
            '^DJI': 'dow'
        }
        
        column_name = symbol_mapping.get(symbol)
        if not column_name:
            return {"error": f"Unsupported index symbol: {symbol}"}
        
        with get_sqlalchemy_engine().connect() as conn:
            # 지수 데이터 조회 (SQLAlchemy 2.x 호환되도록 수정)
            query = text(f"""
                SELECT date, {column_name}
                FROM index_closing_price
                WHERE date BETWEEN :start_date AND :end_date AND {column_name} IS NOT NULL
                ORDER BY date ASC
            """)
            params = {"start_date": start_date, "end_date": end_date}
            result = conn.execute(query, params)
            rows = result.mappings().all()  # 수정된 부분
        
        if not rows:
            return {"error": f"No data found for symbol {symbol}"}
        
        # 데이터 구조화 (딕셔너리 접근 방식으로 변경)
        dates = []
        closes = []
        
        for row in rows:
            # row는 이제 딕셔너리 형태
            if isinstance(row['date'], str):
                dates.append(row['date'])
            else:
                dates.append(row['date'].strftime('%Y-%m-%d'))
            closes.append(float(row[column_name]) if row[column_name] is not None else None)
        
        # index_closing_price 테이블에는 OHLV 데이터가 없으므로 close 값만 제공
        # 호환성을 위해 opens, highs, lows는 closes와 동일한 값으로, volumes는 None으로 설정
        return {
            "dates": dates,
            "closes": closes,
            "opens": closes,  # 데이터베이스에 open 데이터가 없으므로 close와 동일하게 설정
            "highs": closes,  # 데이터베이스에 high 데이터가 없으므로 close와 동일하게 설정
            "lows": closes,   # 데이터베이스에 low 데이터가 없으므로 close와 동일하게 설정
            "volumes": [None] * len(closes)  # 데이터베이스에 volume 데이터가 없음
        }
    except Exception as e:
        return {"error": f"Error fetching index data from database for {symbol}: {e}"}
    
    
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
    DOW, S&P500, NASDAQ 6개월치 일별 종가 데이터를 데이터베이스에서 반환합니다.
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

        with get_sqlalchemy_engine().connect() as conn:
            query = text("""
                SELECT date, dow, sp500, nasdaq 
                FROM index_closing_price 
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date ASC;
            """)
            params = {"start_date": start_str, "end_date": end_str}
            result = conn.execute(query, params)
            rows = result.mappings().all()  # 수정된 부분
        
        # 데이터 구조화 (딕셔너리 접근 방식으로 변경)
        dates = []
        dow_closes = []
        sp500_closes = []
        nasdaq_closes = []
        
        for row in rows:
            if isinstance(row['date'], str):
                dates.append(row['date'])
            else:
                dates.append(row['date'].strftime('%Y-%m-%d'))
            dow_closes.append(float(row['dow']) if row['dow'] is not None else None)
            sp500_closes.append(float(row['sp500']) if row['sp500'] is not None else None)
            nasdaq_closes.append(float(row['nasdaq']) if row['nasdaq'] is not None else None)
        
        result = {
            'dow': {'dates': dates, 'closes': dow_closes},
            'sp500': {'dates': dates, 'closes': sp500_closes},
            'nasdaq': {'dates': dates, 'closes': nasdaq_closes}
        }
        
        return result
        
    except Exception as e:
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
    try:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=365)  # 1년(365일)
        start_str = start_dt.strftime('%Y-%m-%d')
        end_str = end_dt.strftime('%Y-%m-%d')

        with get_sqlalchemy_engine().connect() as conn:
            # SQLAlchemy 2.x 호환되도록 수정
            query = text("""
                SELECT date, dow, sp500, nasdaq 
                FROM index_closing_price 
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date ASC;
            """)
            params = {"start_date": start_str, "end_date": end_str}
            result = conn.execute(query, params)
            rows = result.mappings().all()  # 수정된 부분
        
        # 데이터 구조화 (딕셔너리 접근 방식으로 변경)
        dates = []
        dow_closes = []
        sp500_closes = []
        nasdaq_closes = []
        
        for row in rows:
            # row는 이제 딕셔너리 형태
            if isinstance(row['date'], str):
                dates.append(row['date'])
            else:
                dates.append(row['date'].strftime('%Y-%m-%d'))
            dow_closes.append(float(row['dow']) if row['dow'] is not None else None)
            sp500_closes.append(float(row['sp500']) if row['sp500'] is not None else None)
            nasdaq_closes.append(float(row['nasdaq']) if row['nasdaq'] is not None else None)
        
        result = {
            'dow': {'dates': dates, 'closes': dow_closes},
            'sp500': {'dates': dates, 'closes': sp500_closes},
            'nasdaq': {'dates': dates, 'closes': nasdaq_closes}
        }
        
        return result
        
    except Exception as e:
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

def get_enhanced_stock_info(ticker: str, end_date: str = None) -> Dict:
    """
    데이터베이스에서 주식 정보를 가져와 분석하고, 시가총액/유동주식수 등은 FMP API로 가져옵니다.
    """
    import numpy as np
    try:
        # 티커 첫 글자에 따라 테이블 결정
        first_letter = ticker[0].lower()
        if 'a' <= first_letter <= 'd':
            table_name = 'fnspid_stock_price_a'
        elif 'e' <= first_letter <= 'm':
            table_name = 'fnspid_stock_price_b'
        elif 'n' <= first_letter <= 'z':
            table_name = 'fnspid_stock_price_c'
        else:
            return {"error": f"Invalid ticker format: {ticker}"}
        
        # end_date 파라미터 처리
        if end_date is None:
            # end_date가 제공되지 않으면 기본값으로 2023-12-31 사용
            final_end_date = '2023-12-31'
        else:
            # end_date가 2023년을 넘으면 2023-12-31로 조정
            if end_date > '2023-12-31':
                final_end_date = '2023-12-31'
            else:
                final_end_date = end_date
        
        # 기준 날짜로부터 1년, 1개월, 60일 전 날짜 계산
        start_1y = (datetime.strptime(final_end_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
        start_1m = (datetime.strptime(final_end_date, '%Y-%m-%d') - timedelta(days=31)).strftime('%Y-%m-%d')
        start_60d = (datetime.strptime(final_end_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d')
        
        with get_sqlalchemy_engine().connect() as conn:
            # 1년치 데이터 조회
            query_1y = text(f"""
                SELECT date, open, high, low, close, volume, adj_close
                FROM {table_name}
                WHERE stock_symbol = :ticker AND date BETWEEN :start_date AND :end_date
                ORDER BY date ASC
            """)
            params_1y = {"ticker": ticker, "start_date": start_1y, "end_date": final_end_date}
            result_1y = conn.execute(query_1y, params_1y)
            rows_1y = result_1y.mappings().all()
            
            # 1개월치 데이터 조회
            query_1m = text(f"""
                SELECT date, open, high, low, close, volume, adj_close
                FROM {table_name}
                WHERE stock_symbol = :ticker AND date BETWEEN :start_date AND :end_date
                ORDER BY date ASC
            """)
            params_1m = {"ticker": ticker, "start_date": start_1m, "end_date": final_end_date}
            result_1m = conn.execute(query_1m, params_1m)
            rows_1m = result_1m.mappings().all()
            
            # 60일치 데이터 조회
            query_60d = text(f"""
                SELECT date, open, high, low, close, volume, adj_close
                FROM {table_name}
                WHERE stock_symbol = :ticker AND date BETWEEN :start_date AND :end_date
                ORDER BY date ASC
            """)
            params_60d = {"ticker": ticker, "start_date": start_60d, "end_date": final_end_date}
            result_60d = conn.execute(query_60d, params_60d)
            rows_60d = result_60d.mappings().all()
        
        # 데이터 확인
        if not rows_1y or not rows_1m or not rows_60d:
            return {"error": f"No historical data found for {ticker} in database"}
        
        # DataFrame 생성 (딕셔너리 리스트를 사용하므로 columns 인자 불필요)
        df_1y = pd.DataFrame(rows_1y)
        df_1m = pd.DataFrame(rows_1m)
        df_60d = pd.DataFrame(rows_60d)
        
        # 날짜를 인덱스로 설정하고 정렬
        for df in [df_1y, df_1m, df_60d]:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
        
        # 현재가 (가장 최근 종가) - adj_close 사용
        current_price = df_1y['adj_close'].iloc[-1] if not df_1y.empty else None
        # 52주 최고가/최저가
        week_52_high = df_1y['high'].max() if not df_1y.empty else None
        week_52_low = df_1y['low'].min() if not df_1y.empty else None
        # 60일 평균거래량
        avg_volume_60d = df_60d['volume'].mean() if not df_60d.empty else None
        # 1개월 변동성 (표준편차 기반, 연환산)
        if len(df_1m) > 1:
            returns_1m = df_1m['adj_close'].pct_change().dropna()
            volatility_1m = returns_1m.std() * (252 ** 0.5) * 100
        else:
            volatility_1m = None
        # 1년 변동성 (연환산)
        if len(df_1y) > 1:
            returns_1y = df_1y['adj_close'].pct_change().dropna()
            volatility_1y = returns_1y.std() * (252 ** 0.5) * 100
        else:
            volatility_1y = None
        # 시가총액, 유동주식수 등은 FMP API로 가져오기
        market_cap = None
        shares_outstanding = None
        float_shares = None
        
        # 안전한 숫자 변환 함수
        def safe_int_convert(value):
            if value is None:
                return None
            try:
                return int(float(str(value).replace(',', '')))
            except (ValueError, TypeError):
                return None
        
        # 1단계: FMP Profile API 시도
        try:
            api_key = settings.FMP_API_KEY
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
            print(f"🔍 FMP Profile URL: {url[:50]}...{url[-20:]}")
            resp = requests.get(url)
            print(f"📡 FMP Profile response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"📊 FMP Profile data received: {len(data)} companies")
                if data and isinstance(data, list) and len(data) > 0:
                    company_data = data[0]
                    print(f"🔍 All available keys: {list(company_data.keys())}")
                    
                    market_cap = safe_int_convert(company_data.get('mktCap'))
                    
                    # 여러 필드명 시도
                    shares_fields = ['sharesOutstanding', 'weightedAverageShsOut', 'weightedAverageShares', 'commonStockSharesOutstanding']
                    float_fields = ['floatShares', 'freeFloat', 'float', 'publicFloat', 'tradableShares']
                    
                    for field in shares_fields:
                        if company_data.get(field) and shares_outstanding is None:
                            shares_outstanding = safe_int_convert(company_data.get(field))
                            print(f"✅ Found shares_outstanding in field: {field} = {shares_outstanding}")
                            break
                    
                    for field in float_fields:
                        if company_data.get(field) and float_shares is None:
                            float_shares = safe_int_convert(company_data.get(field))
                            print(f"✅ Found float_shares in field: {field} = {float_shares}")
                            break
                    
                    # float_shares가 없으면 shares_outstanding으로 대체
                    if float_shares is None and shares_outstanding is not None:
                        float_shares = shares_outstanding
                        print(f"📝 Using shares_outstanding as float_shares: {float_shares}")
                    
                    print(f"💰 Final values - MarketCap: {market_cap}, Shares: {shares_outstanding}, Float: {float_shares}")
        except Exception as e:
            print(f"❌ FMP Profile error for {ticker}: {e}")
        
        # 2단계: FMP Key Metrics API 시도 (profile에서 못 가져온 경우)
        if shares_outstanding is None or float_shares is None:
            try:
                metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"
                print(f"🔍 Trying FMP Key Metrics: {metrics_url[:50]}...{metrics_url[-20:]}")
                resp = requests.get(metrics_url)
                if resp.status_code == 200:
                    metrics_data = resp.json()
                    if metrics_data and isinstance(metrics_data, list) and len(metrics_data) > 0:
                        metrics = metrics_data[0]
                        if shares_outstanding is None:
                            shares_outstanding = safe_int_convert(metrics.get('sharesOutstanding'))
                            print(f"✅ Got shares_outstanding from metrics: {shares_outstanding}")
                        if float_shares is None:
                            float_shares = safe_int_convert(metrics.get('freeFloatShares')) or shares_outstanding
                            print(f"✅ Got float_shares from metrics: {float_shares}")
            except Exception as e:
                print(f"❌ FMP Key Metrics error: {e}")
        
        # 3단계: 거래량 기반 추론 (마지막 수단)
        if shares_outstanding is None and avg_volume_60d is not None:
            # 일반적으로 일평균거래량은 유통주식수의 0.1% ~ 5% 정도
            # 보수적으로 1%로 추정
            estimated_shares = int(avg_volume_60d * 100)  # 거래량의 100배로 추정
            shares_outstanding = estimated_shares
            print(f"📊 Estimated shares_outstanding from volume: {shares_outstanding}")
        
        if float_shares is None and shares_outstanding is not None:
            # float_shares가 없으면 shares_outstanding의 80%로 추정 (일반적인 비율)
            float_shares = int(shares_outstanding * 0.8)
            print(f"📊 Estimated float_shares as 80% of outstanding: {float_shares}")
        
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
    FMP API를 통해 재무지표를 가져옵니다.
    - 매출액, 영업이익, 영업이익률, 순이익
    - 최근 2년치 데이터 제공
    
    Note: This function has been replaced with FMP API for better reliability.
    The end_date parameter is kept for compatibility but not used.
    """
    return get_financial_metrics_from_fmp(ticker)

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
