import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List
from app.core.config import settings
from app.db.connection import get_sqlalchemy_engine
import pandas_datareader.data as web

def get_sector_companies_from_db(sector: str) -> List[str]:
    """
    DB에서 특정 섹터에 해당하는 모든 기업의 stock_symbol을 가져옵니다.
    """
    engine = get_sqlalchemy_engine()
    if engine is None:
        return []
    
    try:
        with engine.connect() as conn:
            query = """
                SELECT DISTINCT stock_symbol
                FROM kb_enterprise_dataset
                WHERE sector = %s
                ORDER BY stock_symbol;
            """
            result = conn.execute(query, (sector,))
            rows = result.fetchall()
            return [row[0] for row in rows if row[0]]
    except Exception as e:
        print(f"Error fetching companies for sector {sector}: {e}")
        return []

def get_stock_table_name(ticker: str) -> str:
    """
    ticker의 첫 글자에 따라 적절한 stock price 테이블명을 반환합니다.
    """
    first_char = ticker[0].lower()
    if 'a' <= first_char <= 'd':
        return 'fnspid_stock_price_a'
    elif 'e' <= first_char <= 'm':
        return 'fnspid_stock_price_b'
    else:  # n-z
        return 'fnspid_stock_price_c'


def get_stock_data_from_db(ticker: str, end_date: str, days_back: int = 400) -> Dict:
    """
    DB에서 특정 ticker의 주가 데이터를 가져옵니다.
    """
    engine = get_sqlalchemy_engine()
    try:
        with engine.connect() as conn: # 수정
            table_name = get_stock_table_name(ticker)
            
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            start_dt = end_dt - timedelta(days=days_back)
            
            query = f"""
                SELECT date, open, high, low, close, adj_close, volume
                FROM {table_name}
                WHERE stock_symbol = %s 
                AND date BETWEEN %s AND %s
                ORDER BY date ASC;
            """
            
            result = conn.execute(query, (ticker, start_dt.strftime('%Y-%m-%d'), end_date))
            rows = result.fetchall()
            
            if not rows:
                return {"error": f"No data found for {ticker}"}
            
            data = []
            for row in rows:
                data.append({
                    'date': row[0],
                    'open': float(row[1]) if row[1] else None,
                    'high': float(row[2]) if row[2] else None,
                    'low': float(row[3]) if row[3] else None,
                    'close': float(row[4]) if row[4] else None,
                    'adj close': float(row[5]) if row[5] else None,
                    'volume': int(row[6]) if row[6] else None
                })
            
            return {"data": data}
            
    except Exception as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return {"error": str(e)}

def get_stock_returns(ticker: str, end_date: str) -> Dict:
    """
    특정 기간별 수익률을 계산합니다.
    """
    try:
        stooq_ticker = ticker if ticker.endswith('.US') else ticker + '.US'
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 1년 전 데이터부터 가져오기
        start_dt = end_dt - timedelta(days=400)  # 365일에서 400일로 늘려서 데이터 확보
        df = web.DataReader(stooq_ticker, 'stooq', start=start_dt.strftime('%Y-%m-%d'), end=end_date)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return {"1week": None, "1month": None, "1year": None}
        
        df = df.sort_index()
        current_price = df['Close'].iloc[-1]
        
        # 1주일 수익률 - 더 유연한 날짜 매칭
        week_return = None
        for days_back in range(5, 10):  # 5-9일 전 데이터 중 가장 가까운 것
            week_ago = end_dt - timedelta(days=days_back)
            week_data = df[df.index <= week_ago]
            if not week_data.empty:
                week_price = week_data['Close'].iloc[-1]
                week_return = ((current_price / week_price) - 1) * 100
                break
        
        # 1개월 수익률 - 더 유연한 날짜 매칭
        month_return = None
        for days_back in range(28, 35):  # 28-34일 전 데이터 중 가장 가까운 것
            month_ago = end_dt - timedelta(days=days_back)
            month_data = df[df.index <= month_ago]
            if not month_data.empty:
                month_price = month_data['Close'].iloc[-1]
                month_return = ((current_price / month_price) - 1) * 100
                break
        
        # 1년 수익률 - 더 유연한 날짜 매칭
        year_return = None
        for days_back in range(360, 370):  # 360-369일 전 데이터 중 가장 가까운 것
            year_ago = end_dt - timedelta(days=days_back)
            year_data = df[df.index <= year_ago]
            if not year_data.empty:
                year_price = year_data['Close'].iloc[-1]
                year_return = ((current_price / year_price) - 1) * 100
                break
        
        print(f"Returns for {ticker}: 1W={week_return}, 1M={month_return}, 1Y={year_return}")
        
        return {
            "1week": round(week_return, 2) if week_return else None,
            "1month": round(month_return, 2) if month_return else None,
            "1year": round(year_return, 2) if year_return else None
        }
    except Exception as e:
        print(f"Error calculating returns for {ticker}: {e}")
        return {"1week": None, "1month": None, "1year": None}

def get_valuation_metrics_from_fmp(ticker: str) -> Dict:
    """
    FMP API에서 밸류에이션 지표를 가져옵니다.
    """
    try:
        api_key = settings.FMP_API_KEY
        url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={api_key}"
        resp = requests.get(url)
        time.sleep(0.5)  # API 제한 고려
        
        if resp.status_code != 200:
            return {"pe_ratio": None, "pb_ratio": None, "roe": None}
        
        data = resp.json()
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return {"pe_ratio": None, "pb_ratio": None, "roe": None}
        
        # 최신 데이터 사용
        current_data = data[0]
        
        def safe_float_convert(value):
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        pe_ratio = safe_float_convert(current_data.get('priceEarningsRatio'))
        pb_ratio = safe_float_convert(current_data.get('priceToBookRatio'))
        roe = safe_float_convert(current_data.get('returnOnEquity'))
        
        return {
            "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
            "pb_ratio": round(pb_ratio, 2) if pb_ratio else None,
            "roe": round(roe, 2) if roe else None  # FMP에서는 이미 백분율
        }
    except Exception as e:
        print(f"Error fetching valuation metrics for {ticker}: {e}")
        return {"pe_ratio": None, "pb_ratio": None, "roe": None}

def get_enhanced_stock_info(ticker: str, end_date: str) -> Dict:
    """
    특정 종료일 기준으로 주식 정보를 가져옵니다. (FMP API 사용)
    """
    import numpy as np
    try:
        stooq_ticker = ticker if ticker.endswith('.US') else ticker + '.US'
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 필요한 기간의 데이터 가져오기
        start_dt = end_dt - timedelta(days=30)  # 30일치 데이터
        df = web.DataReader(stooq_ticker, 'stooq', start=start_dt.strftime('%Y-%m-%d'), end=end_date)
        df = df.sort_index()
        
        if df.empty:
            return {"error": f"No historical data found for {ticker}"}
        
        # 현재가 (종료일 기준 종가)
        current_price = df['Close'].iloc[-1]
        
        # 시가총액은 FMP API로 가져오기
        market_cap = None
        shares_outstanding = None
        
        try:
            api_key = settings.FMP_API_KEY
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
            resp = requests.get(url, timeout=10)
            time.sleep(0.5)
            
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
                    
                    print(f"� FMP market cap for {ticker}: {market_cap}")
                else:
                    print(f"❌ FMP: No profile data found for {ticker}")
                    
        except Exception as e:
            print(f"❌ FMP error for {ticker}: {e}")
            # FMP 실패 시 추정값 사용
            estimated_shares = 1000000  # 1백만주 가정
            market_cap = int(current_price * estimated_shares)
            print(f"🔮 Fallback estimated market cap for {ticker}: {market_cap}")
        
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2) if current_price else None,
            "market_cap": market_cap
        }
    except Exception as e:
        return {"error": f"Error fetching enhanced stock info for {ticker}: {e}"}

def get_industry_top10_companies(sector: str, end_date: str) -> Dict:
    """
    특정 산업의 미리 정의된 기업 목록에 대한 정보를 반환합니다. (DB + FMP API 사용)
    """
    try:
        print(f"🚀 Starting industry analysis for sector: {sector}, end_date: {end_date}")
        
        # 섹터별 미리 정의된 기업 목록
        sector_companies = {
            'Technology': ['NVDA', 'MSFT', 'AAPL', 'GOOG', 'META', 'AVGO', 'ORCL', 'PLTR', 'GE', 'IBM', 'CRM', 'AMD', 'INTU', 'TXN'],
            'Telecommunications': ['CSCO', 'TMUS', 'T', 'VZ', 'ANET', 'CMCSA', 'CHTR', 'WBD', 'FFIV', 'LBRDK', 'ROKU'],
            'Health Care': ['LLY', 'JNJ', 'ABBV', 'PM', 'UNH', 'ABT', 'MRK', 'ISRG', 'AMGN', 'BSX', 'SYK', 'PFE', 'GILD'],
            'Finance': ['JPM', 'BAC', 'WFC', 'MS', 'AXP', 'GS', 'BLK', 'SCHW', 'C', 'SPGI'],
            'Real Estate': ['AMT', 'WELL', 'PLD', 'EQIX', 'DLR', 'SPG', 'O', 'PSA', 'CCI', 'VICI', 'EXR'],
            'Consumer Discretionary': ['AMZN', 'TSLA', 'WMT', 'V', 'NFLX', 'MA', 'COST', 'PG', 'HD', 'DIS', 'MCD', 'UBER', 'BKNG'],
            'Consumer Staples': ['KO', 'PEP', 'MDLZ', 'CVS', 'MNST', 'CTVA', 'KR', 'KDP', 'HSY', 'KHC', 'STZ', 'GIS', 'K'],
            'Industrials': ['LIN', 'RTX', 'CAT', 'BA', 'TMO', 'HON', 'DHR', 'UNP', 'DE', 'LMT', 'PH', 'TDG', 'UPS'],
            'Basic Materials': ['SCCO', 'NEM', 'FCX', 'IP', 'MP', 'TREX', 'FBIN', 'LPX', 'UFPI', 'CDE', 'CLF', 'SLVM'],
            'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'MPC', 'PSX', 'MPLX', 'VLO', 'HES', 'OXY', 'FANG', 'EQT', 'EXEEW'],
            'Utilities': ['SO', 'CEG', 'DUK', 'WM', 'RSG', 'WMB', 'EPD', 'VST', 'KMI', 'ET', 'AEP', 'LNG', 'OKE']
        }
        
        # 입력받은 섹터에 해당하는 기업 목록 가져오기
        company_tickers = sector_companies.get(sector, [])
        print(f"📋 Found {len(company_tickers)} companies for sector {sector}: {company_tickers}")
        
        if not company_tickers:
            return {"error": f"No predefined companies found for sector: {sector}"}
        
        companies_data = []
        successful_count = 0
        failed_count = 0
        
        for i, ticker in enumerate(company_tickers):
            try:
                print(f"📊 Processing {i+1}/{len(company_tickers)}: {ticker} (using DB)")
                
                # 기본 정보 (시가총액, 현재가 등) - DB에서 가져오기
                enhanced_info = get_enhanced_stock_info_from_db(ticker, end_date)
                if "error" in enhanced_info:
                    print(f"⚠️  Enhanced info failed for {ticker}: {enhanced_info['error']}")
                    failed_count += 1
                    continue
                
                # 시가총액이 있는 경우만 처리
                if not enhanced_info.get('market_cap'):
                    print(f"⚠️  No market cap for {ticker}")
                    failed_count += 1
                    continue
                
                # 수익률 계산 - DB에서 가져오기
                returns = get_stock_returns_from_db(ticker, end_date)
                
                # 밸류에이션 지표 - 여전히 FMP API 사용
                valuation = get_valuation_metrics_from_fmp(ticker)
                
                company_data = {
                    "ticker": ticker,
                    "current_price": enhanced_info.get('current_price'),
                    "market_cap_millions": round(enhanced_info.get('market_cap', 0) / 1000000, 1),
                    "return_1week": returns.get('1week'),
                    "return_1month": returns.get('1month'),
                    "return_1year": returns.get('1year'),
                    "pe_ratio": valuation.get('pe_ratio'),
                    "pb_ratio": valuation.get('pb_ratio'),
                    "roe": valuation.get('roe')
                }
                companies_data.append(company_data)
                successful_count += 1
                print(f"✅ Successfully processed {ticker} (Market Cap: ${enhanced_info.get('market_cap', 0)/1000000:.1f}M)")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ Error processing {ticker}: {e}")
                continue
        
        print(f"📈 Processing summary: {successful_count} successful, {failed_count} failed")
        
        # 시가총액 기준으로 정렬
        companies_data.sort(key=lambda x: x.get('market_cap_millions', 0) or 0, reverse=True)
        
        print(f"🎯 Successfully processed {len(companies_data)} companies for sector {sector}")
        
        return {
            "sector": sector,
            "end_date": end_date,
            "companies": companies_data,
            "total_companies": len(companies_data)
        }
        
    except Exception as e:
        print(f"💥 Critical error in get_industry_top10_companies: {e}")
        return {"error": f"Error processing industry analysis: {str(e)}"}

def get_stock_returns_from_db(ticker: str, end_date: str) -> Dict:
    """
    DB에서 특정 기간별 수익률을 계산합니다.
    """
    try:
        stock_data = get_stock_data_from_db(ticker, end_date, 400)
        
        if "error" in stock_data:
            print(f"No data found for {ticker}")
            return {"1week": None, "1month": None, "1year": None}
        
        data = stock_data["data"]
        if not data:
            return {"1week": None, "1month": None, "1year": None}
        
        # 최신 가격 (end_date 기준)
        current_price = data[-1]['close']
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 1주일 수익률
        week_return = None
        for days_back in range(5, 10):
            target_date = end_dt - timedelta(days=days_back)
            for row in reversed(data):
                if isinstance(row['date'], str):
                    row_date = datetime.strptime(row['date'], '%Y-%m-%d')
                else:
                    row_date = row['date']
                
                if row_date <= target_date and row['close']:
                    week_price = row['close']
                    week_return = ((current_price / week_price) - 1) * 100
                    break
            if week_return is not None:
                break
        
        # 1개월 수익률
        month_return = None
        for days_back in range(28, 35):
            target_date = end_dt - timedelta(days=days_back)
            for row in reversed(data):
                if isinstance(row['date'], str):
                    row_date = datetime.strptime(row['date'], '%Y-%m-%d')
                else:
                    row_date = row['date']
                
                if row_date <= target_date and row['close']:
                    month_price = row['close']
                    month_return = ((current_price / month_price) - 1) * 100
                    break
            if month_return is not None:
                break
        
        # 1년 수익률
        year_return = None
        for days_back in range(360, 370):
            target_date = end_dt - timedelta(days=days_back)
            for row in reversed(data):
                if isinstance(row['date'], str):
                    row_date = datetime.strptime(row['date'], '%Y-%m-%d')
                else:
                    row_date = row['date']
                
                if row_date <= target_date and row['close']:
                    year_price = row['close']
                    year_return = ((current_price / year_price) - 1) * 100
                    break
            if year_return is not None:
                break
        
        print(f"Returns for {ticker}: 1W={week_return}, 1M={month_return}, 1Y={year_return}")
        
        return {
            "1week": round(week_return, 2) if week_return else None,
            "1month": round(month_return, 2) if month_return else None,
            "1year": round(year_return, 2) if year_return else None
        }
    except Exception as e:
        print(f"Error calculating returns for {ticker}: {e}")
        return {"1week": None, "1month": None, "1year": None}

def get_enhanced_stock_info_from_db(ticker: str, end_date: str) -> Dict:
    """
    DB에서 특정 종료일 기준으로 주식 정보를 가져옵니다.
    """
    try:
        # DB에서 현재가 가져오기
        stock_data = get_stock_data_from_db(ticker, end_date, 30)
        
        if "error" in stock_data:
            return {"error": f"No historical data found for {ticker}"}
        
        data = stock_data["data"]
        if not data:
            return {"error": f"No historical data found for {ticker}"}
        
        # 현재가 (종료일 기준 종가)
        current_price = data[-1]['close']
        
        # 시가총액은 여전히 FMP API로 가져오기
        market_cap = None
        shares_outstanding = None
        
        try:
            api_key = settings.FMP_API_KEY
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
            resp = requests.get(url, timeout=10)
            time.sleep(0.5)
            
            if resp.status_code == 200:
                data_fmp = resp.json()
                if data_fmp and isinstance(data_fmp, list) and len(data_fmp) > 0:
                    company_data = data_fmp[0]
                    
                    def safe_int_convert(value):
                        if value is None:
                            return None
                        try:
                            return int(float(str(value).replace(',', '')))
                        except (ValueError, TypeError):
                            return None
                    
                    market_cap = safe_int_convert(company_data.get('mktCap'))
                    shares_outstanding = safe_int_convert(company_data.get('sharesOutstanding'))
                    
                    print(f"🔵 FMP market cap for {ticker}: {market_cap}")
                else:
                    print(f"❌ FMP: No profile data found for {ticker}")
                    
        except Exception as e:
            print(f"❌ FMP error for {ticker}: {e}")
            # FMP 실패 시 추정값 사용
            estimated_shares = 1000000  # 1백만주 가정
            market_cap = int(current_price * estimated_shares)
            print(f"🔮 Fallback estimated market cap for {ticker}: {market_cap}")
        
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2) if current_price else None,
            "market_cap": market_cap
        }
    except Exception as e:
        return {"error": f"Error fetching enhanced stock info for {ticker}: {e}"}
