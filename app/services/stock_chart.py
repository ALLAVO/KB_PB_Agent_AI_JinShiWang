from datetime import datetime, timedelta
from typing import Dict, List
from app.services.crawler import get_stock_price_chart_data, get_stock_price_chart_with_ma, get_index_chart_data

class StockChartService:
    """주가 차트 관련 서비스"""
    
    @staticmethod
    def get_combined_chart(ticker: str, start_date: str, end_date: str, chart_types: List[str] = ["price"], ma_periods: List[int] = [5, 20, 60]) -> Dict:
        """
        여러 차트 타입을 조합한 데이터를 반환합니다.
        
        Args:
            ticker: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            chart_types: 차트 타입 리스트 (["price", "moving_average", "volume", "relative_nasdaq"])
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
            
            # 나스닥 대비 상대지수 계산
            if "relative_nasdaq" in chart_types:
                nasdaq_data = get_index_chart_data("^IXIC", start_date, end_date)
                if "error" not in nasdaq_data and len(nasdaq_data["closes"]) == len(data["closes"]):
                    stock_closes = data["closes"]
                    nasdaq_closes = nasdaq_data["closes"]
                    
                    # 첫날 기준으로 정규화하여 상대 성과 계산 (포인트 단위)
                    if stock_closes and nasdaq_closes:
                        stock_base = stock_closes[0]
                        nasdaq_base = nasdaq_closes[0]
                        
                        relative_values = []
                        for i in range(len(stock_closes)):
                            stock_change = ((stock_closes[i] / stock_base) - 1) * 100
                            nasdaq_change = ((nasdaq_closes[i] / nasdaq_base) - 1) * 100
                            relative_performance = stock_change - nasdaq_change
                            relative_values.append(relative_performance)
                        
                        result["data"]["relative_nasdaq"] = {
                            "values": relative_values
                        }
            
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
