import pandas_datareader.data as web
from datetime import datetime, timedelta

# 개별 심볼 테스트
symbols = ['^DJI', '^SPX', '^NDQ']
end_date = '2025-01-20'  # 현재 날짜로 변경
start_date = '2024-12-20'

for symbol in symbols:
    try:
        print(f"Testing {symbol}...")
        df = web.DataReader(symbol, 'stooq', start=start_date, end=end_date)
        print(f"✅ {symbol}: {len(df)} rows")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Sample data: {df.head(2)}")
    except Exception as e:
        print(f"❌ {symbol}: {e}")