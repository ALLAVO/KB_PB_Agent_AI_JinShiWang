from sqlalchemy import create_engine, text
from app.core.config import settings
from typing import List, Dict, Optional
import logging
import re
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from app.services.ai_analysis_service import generate_performance_summary
import numpy as np

logger = logging.getLogger(__name__)

def get_database_connection():
    """데이터베이스 연결"""
    try:
        if hasattr(settings, 'USE_SUPABASE') and settings.USE_SUPABASE:
            # Supabase 연결
            database_url = settings.SUPABASE_DATABASE_URL
        else:
            # 로컬 PostgreSQL 연결
            database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        
        engine = create_engine(database_url, pool_pre_ping=True)
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def parse_amount_string(amount_str: str) -> float:
    """
    '약 70억원', '50만원' 같은 문자열을 숫자로 변환합니다.
    """
    if not amount_str or amount_str in ('', 'null', 'NULL', None):
        return 0.0
    
    # 문자열이 이미 숫자인 경우
    try:
        return float(amount_str)
    except (ValueError, TypeError):
        pass
    
    # 한국어 단위가 포함된 문자열 파싱
    amount_str = str(amount_str).strip()
    
    # 숫자와 단위를 추출하는 정규식
    # 예: '약 70억원' -> '70', '억'
    pattern = r'(?:약\s*)?(\d+(?:\.\d+)?)\s*(억|만|천)?원?'
    match = re.search(pattern, amount_str)
    
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        
        # 단위에 따른 곱셈
        if unit == '억':
            return number * 100000000  # 1억 = 100,000,000
        elif unit == '만':
            return number * 10000      # 1만 = 10,000
        elif unit == '천':
            return number * 1000       # 1천 = 1,000
        else:
            return number              # 단위 없음
    
    # 파싱 실패시 0 반환
    logger.warning(f"Could not parse amount string: {amount_str}")
    return 0.0

def get_all_clients() -> List[Dict]:
    """모든 고객 정보를 가져옵니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            query = text("""
                SELECT id, name, sex, age, risk_profile, investment_horizon, total_amount
                FROM virtual_clients_v4
                ORDER BY id
            """)
            result = conn.execute(query)
            clients = []
            for row in result:
                # total_amount를 안전하게 변환
                try:
                    total_amount = parse_amount_string(row[6])
                except Exception as e:
                    logger.warning(f"Error parsing total_amount for client {row[0]}: {row[6]}, error: {e}")
                    total_amount = 0.0
                
                clients.append({
                    "id": row[0],
                    "name": row[1],
                    "sex": row[2],
                    "age": row[3],
                    "risk_profile": row[4],
                    "investment_horizon": row[5],
                    "total_amount": total_amount
                })
            return clients
    except Exception as e:
        logger.error(f"Error fetching all clients: {e}")
        raise

def get_client_by_id(client_id: str) -> Optional[Dict]:
    """특정 고객의 상세 정보를 가져옵니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            query = text("""
                SELECT id, name, sex, age, risk_profile, investment_horizon, 
                       total_amount, memo1, memo2, memo3, benchmark, months_since_last_rebalancing
                FROM virtual_clients_v4
                WHERE id = :client_id
            """)
            result = conn.execute(query, {"client_id": client_id})
            row = result.fetchone()
            
            if row:
                # total_amount를 안전하게 변환
                try:
                    total_amount = parse_amount_string(row[6])
                except Exception as e:
                    logger.warning(f"Error parsing total_amount for client {client_id}: {row[6]}, error: {e}")
                    total_amount = 0.0
                
                return {
                    "id": row[0],
                    "name": row[1],
                    "sex": row[2],
                    "age": row[3],
                    "risk_profile": row[4],
                    "investment_horizon": row[5],
                    "total_amount": total_amount,
                    "memo1": row[7],
                    "memo2": row[8],
                    "memo3": row[9],
                    "benchmark": row[10],
                    "months_since_last_rebalancing": row[11]
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching client {client_id}: {e}")
        raise

def get_client_portfolio(client_id: str) -> List[Dict]:
    """특정 고객의 포트폴리오 정보를 가져옵니다."""
    try:
        engine = get_database_connection()
        with engine.connect() as conn:
            query = text("""
                SELECT stock, quantity, sector
                FROM virtual_clients_portfolio
                WHERE id = :client_id
                ORDER BY stock
            """)
            result = conn.execute(query, {"client_id": client_id})
            portfolio = []
            for row in result:
                portfolio.append({
                    "stock": row[0],
                    "quantity": int(row[1]) if row[1] else 0,
                    "sector": row[2]
                })
            return portfolio
    except Exception as e:
        logger.error(f"Error fetching portfolio for client {client_id}: {e}")
        raise

def calculate_portfolio_return(portfolio: List[Dict], start_date: str, end_date: str) -> float:
    """포트폴리오의 가중평균 수익률을 계산합니다."""
    try:
        total_value_start = 0
        total_value_end = 0
        
        for holding in portfolio:
            symbol = holding['stock']
            quantity = holding['quantity']
            
            if quantity <= 0:
                continue
                
            try:
                # yfinance를 사용하여 주가 데이터 가져오기
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if len(hist) < 2:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue
                
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                
                value_start = start_price * quantity
                value_end = end_price * quantity
                
                total_value_start += value_start
                total_value_end += value_end
                
            except Exception as e:
                logger.warning(f"Error fetching data for {symbol}: {e}")
                continue
        
        if total_value_start > 0:
            return ((total_value_end - total_value_start) / total_value_start) * 100
        else:
            return 0.0
            
    except Exception as e:
        logger.error(f"Error calculating portfolio return: {e}")
        return 0.0

def calculate_benchmark_return(benchmark: str, start_date: str, end_date: str) -> float:
    """벤치마크의 수익률을 계산합니다."""
    try:
        # 벤치마크 심볼 매핑 (더 정확한 심볼 사용)
        benchmark_symbols = {
            'S&P 500': '^GSPC',
            'S&P500': '^GSPC',
            'SP500': '^GSPC',
            'NASDAQ': '^IXIC',
            'NASDAQ 100': '^NDX',
            'DOW': '^DJI',
            'Dow Jones': '^DJI',
            'Russell 2000': '^RUT',
            'VTI': 'VTI',
            'SPY': 'SPY',
            'QQQ': 'QQQ',
            'MSCI World': 'URTH',
            'Total Stock Market': 'VTI'
        }
        
        # 벤치마크 심볼 결정
        symbol = benchmark_symbols.get(benchmark, benchmark)
        
        # 날짜 형식 확인 및 조정
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 주말을 고려하여 시작일을 조금 앞당김
        extended_start = start_dt - timedelta(days=5)
        extended_end = end_dt + timedelta(days=5)
        
        logger.info(f"Fetching benchmark data for {symbol} ({benchmark}) from {extended_start.date()} to {extended_end.date()}")
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(
            start=extended_start.strftime('%Y-%m-%d'), 
            end=extended_end.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if hist.empty:
            logger.warning(f"No benchmark data found for {symbol}")
            return 0.0
        
        # 실제 요청 기간에 가장 가까운 데이터 찾기
        hist = hist.dropna()
        if len(hist) < 2:
            logger.warning(f"Insufficient benchmark data for {symbol} (only {len(hist)} points)")
            return 0.0
        
        # 시작일과 종료일에 가장 가까운 데이터 포인트 찾기
        start_idx = 0
        end_idx = len(hist) - 1
        
        # 실제 거래일 기준으로 가장 가까운 날짜 찾기
        for i, date in enumerate(hist.index):
            if date.date() >= start_dt.date():
                start_idx = i
                break
        
        for i in range(len(hist) - 1, -1, -1):
            if hist.index[i].date() <= end_dt.date():
                end_idx = i
                break
        
        if start_idx >= end_idx:
            logger.warning(f"Invalid date range for benchmark {symbol}: start_idx={start_idx}, end_idx={end_idx}")
            return 0.0
        
        start_price = hist['Close'].iloc[start_idx]
        end_price = hist['Close'].iloc[end_idx]
        
        if start_price <= 0:
            logger.warning(f"Invalid start price for benchmark {symbol}: {start_price}")
            return 0.0
        
        return_pct = ((end_price - start_price) / start_price) * 100
        
        logger.info(f"Benchmark {symbol} return: {return_pct:.2f}% (from {start_price:.2f} to {end_price:.2f})")
        return return_pct
        
    except Exception as e:
        logger.error(f"Error calculating benchmark return for {benchmark}: {e}")
        return 0.0

def get_client_performance_analysis(client_id: str, period_end_date: str) -> Dict:
    """고객의 성과 분석 데이터를 반환합니다."""
    try:
        # 고객 정보 가져오기
        client_info = get_client_by_id(client_id)
        if not client_info:
            return {"error": f"Client with id {client_id} not found"}
        
        # 포트폴리오 가져오기
        portfolio = get_client_portfolio(client_id)
        if not portfolio:
            return {"error": "No portfolio found for client"}
        
        # 날짜 계산
        period_end = datetime.strptime(period_end_date, '%Y-%m-%d')
        
        # 1주일 전 날짜
        week_start = period_end - timedelta(days=7)
        week_start_str = week_start.strftime('%Y-%m-%d')
        
        # 성과구간 시작 날짜 (리밸런싱 이후)
        months_since_rebalancing = client_info.get('months_since_last_rebalancing', 3)
        performance_start = period_end - timedelta(days=months_since_rebalancing * 30)
        performance_start_str = performance_start.strftime('%Y-%m-%d')
        
        # 벤치마크 정보
        benchmark = client_info.get('benchmark', 'S&P 500')
        
        # 벤치마크 표시명 매핑
        benchmark_display_names = {
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ Composite',
            '^NDX': 'NASDAQ 100',
            '^DJI': 'Dow Jones Industrial Average',
            '^RUT': 'Russell 2000',
            'VTI': 'Total Stock Market (VTI)',
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust'
        }
        
        benchmark_display = benchmark_display_names.get(benchmark, benchmark)
        
        logger.info(f"Calculating performance for client {client_id} with benchmark {benchmark} ({benchmark_display})")
        logger.info(f"Portfolio contains {len(portfolio)} holdings")
        
        # 수익률 계산
        # 1주일 수익률
        weekly_portfolio_return = calculate_portfolio_return(portfolio, week_start_str, period_end_date)
        weekly_benchmark_return = calculate_benchmark_return(benchmark, week_start_str, period_end_date)
        
        # 성과구간 수익률
        performance_portfolio_return = calculate_portfolio_return(portfolio, performance_start_str, period_end_date)
        performance_benchmark_return = calculate_benchmark_return(benchmark, performance_start_str, period_end_date)
        
        # 수익률 계산 결과 로깅
        logger.info(f"Weekly returns - Portfolio: {weekly_portfolio_return:.2f}%, Benchmark: {weekly_benchmark_return:.2f}%")
        logger.info(f"Performance returns - Portfolio: {performance_portfolio_return:.2f}%, Benchmark: {performance_benchmark_return:.2f}%")
        
        # 벤치마크 데이터 검증
        if weekly_benchmark_return == 0.0 and performance_benchmark_return == 0.0:
            logger.warning(f"Benchmark returns are both 0.0 - this might indicate data fetching issues for {benchmark}")
        
        performance_data = {
            "client_name": client_info['name'],
            "benchmark": benchmark_display,
            "benchmark_symbol": benchmark,
            "period_end": period_end_date,
            "performance_period_months": months_since_rebalancing,
            "weekly_return": {
                "portfolio": round(weekly_portfolio_return, 2),
                "benchmark": round(weekly_benchmark_return, 2)
            },
            "performance_return": {
                "portfolio": round(performance_portfolio_return, 2), 
                "benchmark": round(performance_benchmark_return, 2)
            },
            "dates": {
                "week_start": week_start_str,
                "performance_start": performance_start_str,
                "period_end": period_end_date
            },
            "debug_info": {
                "portfolio_holdings": len(portfolio),
                "benchmark_symbol_used": benchmark,
                "benchmark_display_name": benchmark_display
            }
        }
        
        # AI 요약 생성
        try:
            ai_analysis = generate_performance_summary(performance_data)
            performance_data["ai_summary"] = ai_analysis.get("summary", "")
            performance_data["ai_comment"] = ai_analysis.get("comment", "")
        except Exception as e:
            logger.warning(f"Failed to generate AI summary for client {client_id}: {e}")
            performance_data["ai_summary"] = ""
            performance_data["ai_comment"] = ""
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error calculating client performance for {client_id}: {e}")
        return {"error": f"Error calculating performance: {str(e)}"}

def calculate_stock_metrics(symbol: str, period_end_date: str) -> Dict:
    """개별 종목의 현재가, 수익률, 변동성을 계산합니다."""
    try:
        period_end = datetime.strptime(period_end_date, '%Y-%m-%d')
        
        # 1주일 전, 1달 전, 3년 전 날짜 계산
        week_ago = period_end - timedelta(days=7)
        month_ago = period_end - timedelta(days=30)
        three_years_ago = period_end - timedelta(days=3*365)
        
        # yfinance로 데이터 가져오기
        ticker = yf.Ticker(symbol)
        
        # 3년치 데이터 (변동성 계산용)
        hist_3y = ticker.history(
            start=three_years_ago.strftime('%Y-%m-%d'),
            end=(period_end + timedelta(days=1)).strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if hist_3y.empty:
            logger.warning(f"No data found for {symbol}")
            return {
                "current_price": 0.0,
                "weekly_return": 0.0,
                "monthly_return": 0.0,
                "volatility": 0.0,
                "error": f"No data available for {symbol}"
            }
        
        # 현재가 (기준일 종가)
        current_price = hist_3y['Close'].iloc[-1] if len(hist_3y) > 0 else 0.0
        
        # 1주일 수익률
        weekly_return = 0.0
        try:
            week_price = None
            for i in range(min(10, len(hist_3y))):  # 최대 10일 전까지 검색
                check_date = period_end - timedelta(days=7+i)
                date_str = check_date.strftime('%Y-%m-%d')
                if date_str in hist_3y.index.strftime('%Y-%m-%d'):
                    week_price = hist_3y.loc[hist_3y.index.strftime('%Y-%m-%d') == date_str, 'Close'].iloc[0]
                    break
            
            if week_price and week_price > 0:
                weekly_return = ((current_price - week_price) / week_price) * 100
        except Exception as e:
            logger.warning(f"Error calculating weekly return for {symbol}: {e}")
        
        # 1달 수익률
        monthly_return = 0.0
        try:
            month_price = None
            for i in range(min(10, len(hist_3y))):  # 최대 10일 전까지 검색
                check_date = period_end - timedelta(days=30+i)
                date_str = check_date.strftime('%Y-%m-%d')
                if date_str in hist_3y.index.strftime('%Y-%m-%d'):
                    month_price = hist_3y.loc[hist_3y.index.strftime('%Y-%m-%d') == date_str, 'Close'].iloc[0]
                    break
            
            if month_price and month_price > 0:
                monthly_return = ((current_price - month_price) / month_price) * 100
        except Exception as e:
            logger.warning(f"Error calculating monthly return for {symbol}: {e}")
        
        # 변동성 계산 (3년치 데이터 사용)
        volatility = 0.0
        try:
            if len(hist_3y) > 1:
                # 일일 수익률 계산
                daily_returns = hist_3y['Close'].pct_change().dropna()
                
                if len(daily_returns) > 1:
                    # 일일 표준편차 계산
                    daily_std = daily_returns.std()
                    # 월간 변동성으로 환산 (루트20 적용)
                    volatility = daily_std * np.sqrt(20) * 100  # 퍼센트로 변환
        except Exception as e:
            logger.warning(f"Error calculating volatility for {symbol}: {e}")
        
        return {
            "current_price": round(current_price, 2),
            "weekly_return": round(weekly_return, 2),
            "monthly_return": round(monthly_return, 2),
            "volatility": round(volatility, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating stock metrics for {symbol}: {e}")
        return {
            "current_price": 0.0,
            "weekly_return": 0.0,
            "monthly_return": 0.0,
            "volatility": 0.0,
            "error": str(e)
        }

def get_enhanced_client_portfolio(client_id: str, period_end_date: str) -> List[Dict]:
    """비중, 수익률, 변동성이 포함된 포트폴리오 정보를 가져옵니다."""
    try:
        # 기본 포트폴리오 가져오기
        portfolio = get_client_portfolio(client_id)
        
        if not portfolio:
            return []
        
        enhanced_portfolio = []
        total_portfolio_value = 0.0
        
        # 1단계: 각 종목의 현재 시가총액 계산
        for holding in portfolio:
            stock_metrics = calculate_stock_metrics(holding['stock'], period_end_date)
            current_value = stock_metrics['current_price'] * holding['quantity']
            total_portfolio_value += current_value
            
            enhanced_holding = {
                **holding,
                'current_price': stock_metrics['current_price'],
                'current_value': current_value,
                'weekly_return': stock_metrics['weekly_return'],
                'monthly_return': stock_metrics['monthly_return'],
                'volatility': stock_metrics['volatility']
            }
            enhanced_portfolio.append(enhanced_holding)
        
        # 2단계: 비중 계산
        for holding in enhanced_portfolio:
            if total_portfolio_value > 0:
                holding['weight'] = (holding['current_value'] / total_portfolio_value) * 100
            else:
                holding['weight'] = 0.0
            holding['weight'] = round(holding['weight'], 2)
        
        # 3단계: 비중 순으로 정렬
        enhanced_portfolio.sort(key=lambda x: x['weight'], reverse=True)
        
        return enhanced_portfolio
        
    except Exception as e:
        logger.error(f"Error getting enhanced portfolio for client {client_id}: {e}")
        raise

def get_client_summary(client_id: str, period_end_date: str = None) -> Dict:
    """고객의 종합 정보 (기본정보 + 포트폴리오)를 가져옵니다."""
    try:
        client_info = get_client_by_id(client_id)
        if not client_info:
            return {"error": f"Client with id {client_id} not found"}
        
        # 기준 날짜가 없으면 현재 날짜 사용
        if not period_end_date:
            period_end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 향상된 포트폴리오 정보 가져오기
        enhanced_portfolio = get_enhanced_client_portfolio(client_id, period_end_date)
        
        # 기본 포트폴리오 요약 계산
        total_stocks = len(enhanced_portfolio)
        sectors = list(set([item["sector"] for item in enhanced_portfolio if item["sector"]]))
        total_quantity = sum([item["quantity"] for item in enhanced_portfolio])
        
        return {
            "client_info": client_info,
            "portfolio": enhanced_portfolio,
            "portfolio_summary": {
                "total_stocks": total_stocks,
                "sectors": sectors,
                "total_quantity": total_quantity
            }
        }
    except Exception as e:
        logger.error(f"Error fetching client summary for {client_id}: {e}")
        raise
