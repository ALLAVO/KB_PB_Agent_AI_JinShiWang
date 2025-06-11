import yfinance as yf

if __name__ == "__main__":
    ticker = "AAPL"
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        print(f"Company name: {info.get('longName') or info.get('shortName') or ticker}")
        print(f"Industry: {info.get('industry')}")
        print(f"Website: {info.get('website')}")
    except Exception as e:
        print(f"Error: {e}")
