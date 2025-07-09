#!/usr/bin/env python3
"""
수익률 분석 API 테스트 스크립트
"""
import requests
import json
from datetime import datetime, timedelta

def test_return_analysis_table():
    """수익률 분석 표 데이터 테스트"""
    # 더 긴 기간으로 테스트 (18개월)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=547)).strftime('%Y-%m-%d')  # 18개월 전
    
    url = "http://localhost:8000/api/v1/return-analysis/table"
    params = {
        "symbol": "AAPL",
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        print(f"Testing return analysis table for AAPL ({start_date} ~ {end_date})")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 호출 성공")
            
            if data.get('success'):
                table_data = data['data']['table_data']
                print(f"📊 테이블 데이터 ({len(table_data)} 항목):")
                
                for item in table_data:
                    period = item['period']
                    abs_return = item['absolute_return']
                    rel_return = item['relative_return']
                    
                    abs_str = f"{abs_return:.1f}%" if abs_return is not None else "N/A"
                    rel_str = f"{rel_return:.1f}%" if rel_return is not None else "N/A"
                    
                    print(f"  {period}: 절대수익률={abs_str}, 상대수익률={rel_str}")
                
                # 6M과 12M 데이터 확인
                periods_to_check = ['6M', '12M']
                for period in periods_to_check:
                    period_data = next((item for item in table_data if item['period'] == period), None)
                    if period_data:
                        if period_data['absolute_return'] is not None:
                            print(f"✅ {period} 데이터 정상: 절대수익률={period_data['absolute_return']:.1f}%")
                        else:
                            print(f"⚠️ {period} 데이터 없음 (데이터 부족)")
                    else:
                        print(f"❌ {period} 데이터 누락")
                        
            else:
                print(f"❌ API 에러: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP 에러: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 요청 실패: {e}")

if __name__ == "__main__":
    test_return_analysis_table()
