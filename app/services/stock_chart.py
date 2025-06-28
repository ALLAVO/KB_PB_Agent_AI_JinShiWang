from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.services.crawler import get_stock_price_chart_data, get_stock_price_chart_with_ma

class StockChartService:
    """주가 차트 관련 서비스"""
    
    @staticmethod
    def get_price_chart(ticker: str, start_date: str, end_date: str, chart_type: str = "price") -> Dict:
        """
        주가 차트 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            chart_type: 차트 타입 ("price", "volume", "candlestick")
        
        Returns:
            Dict: 차트 데이터
        """
        try:
            data = get_stock_price_chart_data(ticker, start_date, end_date)
            if "error" in data:
                return data
            
            if chart_type == "price":
                return {
                    "dates": data["dates"],
                    "closes": data["closes"],
                    "chart_type": "line"
                }
            elif chart_type == "volume":
                return {
                    "dates": data["dates"],
                    "volumes": data["volumes"],
                    "chart_type": "bar"
                }
            elif chart_type == "candlestick":
                return {
                    "dates": data["dates"],
                    "opens": data["opens"],
                    "highs": data["highs"],
                    "lows": data["lows"],
                    "closes": data["closes"],
                    "chart_type": "candlestick"
                }
            else:
                return {"error": f"Unsupported chart type: {chart_type}"}
                
        except Exception as e:
            return {"error": f"Error generating price chart: {e}"}
    
    @staticmethod
    def get_ma_chart(ticker: str, start_date: str, end_date: str, ma_periods: List[int] = [5, 20, 60]) -> Dict:
        """
        이동평균이 포함된 주가 차트 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            ma_periods: 이동평균 기간 리스트
        
        Returns:
            Dict: 이동평균 차트 데이터
        """
        try:
            data = get_stock_price_chart_with_ma(ticker, start_date, end_date, ma_periods)
            if "error" in data:
                return data
            
            result = {
                "dates": data["dates"],
                "closes": data["closes"],
                "chart_type": "line_with_ma",
                "ma_data": {}
            }
            
            # 이동평균 데이터 추가
            for period in ma_periods:
                if f'ma{period}' in data:
                    result["ma_data"][f"ma{period}"] = data[f'ma{period}']
            
            return result
            
        except Exception as e:
            return {"error": f"Error generating MA chart: {e}"}
    
    @staticmethod
    def get_period_chart(ticker: str, end_date: str, period: str = "1M") -> Dict:
        """
        기간별 주가 차트 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            end_date: 기준일 (YYYY-MM-DD)
            period: 기간 ("1W", "1M", "3M", "6M", "1Y")
        
        Returns:
            Dict: 기간별 차트 데이터
        """
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # 기간에 따른 시작일 계산
            period_days = {
                "1W": 7,
                "1M": 30,
                "3M": 90,
                "6M": 180,
                "1Y": 365
            }
            
            if period not in period_days:
                return {"error": f"Unsupported period: {period}"}
            
            days = period_days[period]
            start_dt = end_dt - timedelta(days=days)
            start_date = start_dt.strftime('%Y-%m-%d')
            
            # 기간에 따라 적절한 이동평균 선택
            if period in ["1W", "1M"]:
                ma_periods = [5, 10]
            elif period in ["3M"]:
                ma_periods = [5, 20]
            else:  # 6M, 1Y
                ma_periods = [5, 20, 60]
            
            return StockChartService.get_ma_chart(ticker, start_date, end_date, ma_periods)
            
        except Exception as e:
            return {"error": f"Error generating period chart: {e}"}
    
    @staticmethod
    def get_moving_average_only(ticker: str, start_date: str, end_date: str, ma_periods: List[int] = [5, 20, 60]) -> Dict:
        """
        이동평균 데이터만을 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            ma_periods: 이동평균 기간 리스트
        
        Returns:
            Dict: 이동평균 데이터
        """
        try:
            data = get_stock_price_chart_with_ma(ticker, start_date, end_date, ma_periods)
            if "error" in data:
                return data
            
            result = {
                "dates": data["dates"],
                "chart_type": "moving_average",
                "ma_data": {}
            }
            
            # 이동평균 데이터만 추가
            for period in ma_periods:
                if f'ma{period}' in data:
                    result["ma_data"][f"ma{period}"] = data[f'ma{period}']
            
            return result
            
        except Exception as e:
            return {"error": f"Error generating moving average data: {e}"}

    @staticmethod
    def get_volume_only(ticker: str, start_date: str, end_date: str) -> Dict:
        """
        거래량 데이터만을 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        
        Returns:
            Dict: 거래량 데이터
        """
        try:
            data = get_stock_price_chart_data(ticker, start_date, end_date)
            if "error" in data:
                return data
            
            return {
                "dates": data["dates"],
                "volumes": data["volumes"],
                "chart_type": "volume"
            }
            
        except Exception as e:
            return {"error": f"Error generating volume data: {e}"}

    @staticmethod
    def get_combined_chart(ticker: str, start_date: str, end_date: str, chart_types: List[str] = ["price"], ma_periods: List[int] = [5, 20, 60]) -> Dict:
        """
        여러 차트 타입을 조합한 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            chart_types: 차트 타입 리스트 (["price", "moving_average", "volume"])
            ma_periods: 이동평균 기간 리스트
        
        Returns:
            Dict: 조합된 차트 데이터
        """
        try:
            # 기본 주가 데이터 가져오기
            data = get_stock_price_chart_data(ticker, start_date, end_date)
            if "error" in data:
                return data
            
            result = {
                "dates": data["dates"],
                "chart_types": chart_types,
                "data": {}
            }
            
            # 요청된 차트 타입에 따라 데이터 추가
            if "price" in chart_types:
                result["data"]["price"] = {
                    "closes": data["closes"],
                    "opens": data["opens"],
                    "highs": data["highs"],
                    "lows": data["lows"]
                }
            
            if "volume" in chart_types:
                result["data"]["volume"] = {
                    "volumes": data["volumes"]
                }
            
            if "moving_average" in chart_types:
                ma_data = get_stock_price_chart_with_ma(ticker, start_date, end_date, ma_periods)
                if "error" not in ma_data:
                    result["data"]["moving_average"] = {}
                    for period in ma_periods:
                        if f'ma{period}' in ma_data:
                            result["data"]["moving_average"][f"ma{period}"] = ma_data[f'ma{period}']
            
            return result
            
        except Exception as e:
            return {"error": f"Error generating combined chart: {e}"}

    @staticmethod
    def get_chart_summary(ticker: str, start_date: str, end_date: str) -> Dict:
        """
        주가 차트의 요약 정보를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        
        Returns:
            Dict: 차트 요약 정보
        """
        try:
            data = get_stock_price_chart_data(ticker, start_date, end_date)
            if "error" in data:
                return data
            
            closes = data["closes"]
            volumes = data["volumes"]
            
            if not closes:
                return {"error": "No price data available"}
            
            start_price = closes[0]
            end_price = closes[-1]
            change = end_price - start_price
            change_pct = (change / start_price) * 100 if start_price != 0 else 0
            
            return {
                "ticker": ticker,
                "period": f"{start_date} ~ {end_date}",
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "high": round(max(data["highs"]), 2),
                "low": round(min(data["lows"]), 2),
                "avg_volume": round(sum(volumes) / len(volumes), 0) if volumes else 0,
                "data_points": len(closes)
            }
            
        except Exception as e:
            return {"error": f"Error generating chart summary: {e}"}
