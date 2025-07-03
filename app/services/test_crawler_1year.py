import os
from datetime import datetime
from app.services.crawler import get_us_treasury_yields_1year, get_kr_fx_rates_1year

# 환경 변수에서 FRED API 키를 가져옵니다.
FRED_API_KEY = os.environ.get('FRED_API_KEY', 'YOUR_FRED_API_KEY')  # 실제 테스트 시 환경변수로 설정 권장

def test_get_us_treasury_yields_1year():
    today = datetime.today().strftime('%Y-%m-%d')
    result = get_us_treasury_yields_1year(FRED_API_KEY, today)
    print('US Treasury Yields 1 Year:', result)
    assert 'dates' in result and 'us_2y' in result and 'us_10y' in result
    assert len(result['dates']) > 300  # 1년치 데이터가 충분히 있는지

def test_get_kr_fx_rates_1year():
    today = datetime.today().strftime('%Y-%m-%d')
    result = get_kr_fx_rates_1year(today)
    print('KR FX Rates 1 Year:', result)
    assert 'dates' in result and 'usd_krw' in result and 'eur_usd' in result
    assert len(result['dates']) > 300

if __name__ == '__main__':
    test_get_us_treasury_yields_1year()
    test_get_kr_fx_rates_1year()
