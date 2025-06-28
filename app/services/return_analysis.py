from datetime import datetime
from typing import Dict
from app.services.crawler import get_stock_price_chart_data, get_index_chart_data

class ReturnAnalysisService:
    """수익률 분석 관련 서비스"""
    
    @staticmethod
    def get_return_comparison(ticker: str, start_date: str, end_date: str) -> Dict:
        """
        개별 주식과 나스닥의 수익률 비교 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        
        Returns:
            Dict: 수익률 비교 데이터
        """
        try:
            # 주식 데이터 가져오기
            stock_data = get_stock_price_chart_data(ticker, start_date, end_date)
            if "error" in stock_data:
                return stock_data
            
            # 나스닥 지수 데이터 가져오기
            nasdaq_data = get_index_chart_data("^IXIC", start_date, end_date)
            if "error" in nasdaq_data:
                return nasdaq_data
            
            # 수익률 계산
            stock_closes = stock_data["closes"]
            nasdaq_closes = nasdaq_data["closes"]
            
            if len(stock_closes) != len(nasdaq_closes):
                return {"error": "Date mismatch between stock and index data"}
            
            stock_returns = []
            nasdaq_returns = []
            
            for i in range(1, len(stock_closes)):
                stock_return = ((stock_closes[i] / stock_closes[i-1]) - 1) * 100
                nasdaq_return = ((nasdaq_closes[i] / nasdaq_closes[i-1]) - 1) * 100
                stock_returns.append(stock_return)
                nasdaq_returns.append(nasdaq_return)
            
            return {
                "dates": stock_data["dates"][1:],  # 첫 번째 날짜 제외 (수익률 계산 불가)
                "stock_returns": stock_returns,
                "nasdaq_returns": nasdaq_returns,
                "stock_symbol": ticker,
                "nasdaq_symbol": "^IXIC"
            }
            
        except Exception as e:
            return {"error": f"Error in return comparison: {e}"}
    
    @staticmethod
    def get_analysis_summary(ticker: str, start_date: str, end_date: str) -> Dict:
        """
        수익률 분석 요약 정보를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        
        Returns:
            Dict: 분석 요약 정보
        """
        try:
            comparison_data = ReturnAnalysisService.get_return_comparison(ticker, start_date, end_date)
            if "error" in comparison_data:
                return comparison_data
            
            stock_returns = comparison_data["stock_returns"]
            nasdaq_returns = comparison_data["nasdaq_returns"]
            
            # 누적 수익률 계산
            stock_cumulative = sum(stock_returns)
            nasdaq_cumulative = sum(nasdaq_returns)
            outperformance = stock_cumulative - nasdaq_cumulative
            
            # 변동성 계산 (표준편차)
            import statistics
            stock_volatility = statistics.stdev(stock_returns) if len(stock_returns) > 1 else 0
            nasdaq_volatility = statistics.stdev(nasdaq_returns) if len(nasdaq_returns) > 1 else 0
            
            return {
                "period": f"{start_date} ~ {end_date}",
                "stock_return": round(stock_cumulative, 2),
                "nasdaq_return": round(nasdaq_cumulative, 2),
                "outperformance": round(outperformance, 2),
                "stock_volatility": round(stock_volatility, 2),
                "nasdaq_volatility": round(nasdaq_volatility, 2),
                "relative_return": round(outperformance, 2)
            }
            
        except Exception as e:
            return {"error": f"Error in analysis summary: {e}"}
    
    @staticmethod
    def get_combined_chart_data(ticker: str, start_date: str, end_date: str) -> Dict:
        """
        차트용 결합된 수익률 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        
        Returns:
            Dict: 차트용 결합 데이터
        """
        try:
            # 주식 데이터 가져오기
            stock_data = get_stock_price_chart_data(ticker, start_date, end_date)
            if "error" in stock_data:
                return stock_data
            
            # 나스닥 지수 데이터 가져오기
            nasdaq_data = get_index_chart_data("^IXIC", start_date, end_date)
            if "error" in nasdaq_data:
                return nasdaq_data
            
            stock_closes = stock_data["closes"]
            nasdaq_closes = nasdaq_data["closes"]
            dates = stock_data["dates"]
            
            if len(stock_closes) != len(nasdaq_closes):
                return {"error": "Date mismatch between stock and index data"}
            
            # 기준점을 100으로 하는 지수 계산
            stock_base = stock_closes[0]
            nasdaq_base = nasdaq_closes[0]
            
            stock_index = []
            nasdaq_index = []
            relative_index = []
            stock_returns = []
            nasdaq_returns = []
            relative_returns = []
            
            for i, (stock_price, nasdaq_price) in enumerate(zip(stock_closes, nasdaq_closes)):
                # 지수 계산 (기준=100)
                stock_idx = (stock_price / stock_base) * 100
                nasdaq_idx = (nasdaq_price / nasdaq_base) * 100
                relative_idx = stock_idx - nasdaq_idx + 100  # 상대 지수
                
                stock_index.append(stock_idx)
                nasdaq_index.append(nasdaq_idx)
                relative_index.append(relative_idx)
                
                # 수익률 계산 (첫째 날은 0%)
                if i == 0:
                    stock_returns.append(0)
                    nasdaq_returns.append(0)
                    relative_returns.append(0)
                else:
                    stock_ret = ((stock_price / stock_closes[i-1]) - 1) * 100
                    nasdaq_ret = ((nasdaq_price / nasdaq_closes[i-1]) - 1) * 100
                    relative_ret = stock_ret - nasdaq_ret
                    
                    stock_returns.append(stock_ret)
                    nasdaq_returns.append(nasdaq_ret)
                    relative_returns.append(relative_ret)
            
            # 요약 정보 계산
            total_stock_return = ((stock_closes[-1] / stock_closes[0]) - 1) * 100
            total_nasdaq_return = ((nasdaq_closes[-1] / nasdaq_closes[0]) - 1) * 100
            total_outperformance = total_stock_return - total_nasdaq_return
            
            import statistics
            stock_volatility = statistics.stdev(stock_returns[1:]) if len(stock_returns) > 1 else 0
            
            return {
                "chart_data": {
                    "dates": dates,
                    "stock_index": stock_index,
                    "nasdaq_index": nasdaq_index,
                    "relative_index": relative_index,
                    "stock_returns": stock_returns,
                    "nasdaq_returns": nasdaq_returns,
                    "relative_returns": relative_returns
                },
                "summary": {
                    "period": f"{start_date} ~ {end_date}",
                    "stock_return": round(total_stock_return, 2),
                    "nasdaq_return": round(total_nasdaq_return, 2),
                    "outperformance": round(total_outperformance, 2),
                    "stock_volatility": round(stock_volatility, 2),
                    "relative_return": round(total_outperformance, 2)
                }
            }
            
        except Exception as e:
            return {"error": f"Error generating combined chart data: {e}"}
