from typing import Dict
from app.services.crawler import calculate_absolute_and_relative_returns, get_return_analysis_summary

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
            return calculate_absolute_and_relative_returns(ticker, start_date, end_date)
        except Exception as e:
            return {"error": f"Error in return comparison service: {e}"}

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
            return get_return_analysis_summary(ticker, start_date, end_date)
        except Exception as e:
            return {"error": f"Error in analysis summary service: {e}"}

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
            comparison_data = calculate_absolute_and_relative_returns(ticker, start_date, end_date)
            if "error" in comparison_data:
                return comparison_data
            
            summary_data = get_return_analysis_summary(ticker, start_date, end_date)
            if "error" in summary_data:
                return summary_data
            
            return {
                "chart_data": comparison_data,
                "summary": summary_data,
                "ticker": ticker,
                "period": f"{start_date} ~ {end_date}"
            }
        except Exception as e:
            return {"error": f"Error in combined chart data service: {e}"}
