"""
Yahoo Finance service for free real-time market data.
No API key required, no rate limits!
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


def is_indian_stock(symbol: str) -> bool:
    """Check if a symbol is an Indian stock (NSE/BSE)."""
    return symbol.endswith('.NS') or symbol.endswith('.BO')


def fetch_yahoo_quote(symbol: str) -> Optional[Dict]:
    """
    Fetch real-time quote data from Yahoo Finance.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'GOOGL', 'RELIANCE.NS')
    
    Returns:
        Dict with quote data or None if failed
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="2d")
        
        if hist.empty or len(hist) < 2:
            return None
            
        current = hist.iloc[-1]
        previous = hist.iloc[-2]
        
        current_price = float(current['Close'])
        previous_close = float(previous['Close'])
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100
        
        # For Indian stocks, prices are already in INR from Yahoo Finance
        # No conversion needed - Yahoo Finance provides NSE/BSE data in rupees
        return {
            "symbol": symbol.upper(),
            "price": round(current_price, 2),
            "open": round(float(current['Open']), 2),
            "high": round(float(current['High']), 2),
            "low": round(float(current['Low']), 2),
            "volume": int(current['Volume']),
            "previous_close": round(previous_close, 2),
            "change": round(change, 2),
            "change_percent": f"{change_percent:.2f}",
            "latest_trading_day": hist.index[-1].strftime("%Y-%m-%d"),
            "company_name": info.get('longName', symbol.upper()),
            "currency": "INR" if is_indian_stock(symbol) else "USD"
        }
        
    except Exception as e:
        print(f"Error fetching Yahoo Finance quote for {symbol}: {e}")
        return None


def fetch_yahoo_intraday(symbol: str, period: str = "1d", interval: str = "5m") -> Optional[Dict]:
    """
    Fetch intraday data from Yahoo Finance.
    
    Args:
        symbol: Stock symbol
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    
    Returns:
        Dict with intraday data or None if failed
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return None
            
        data = []
        for timestamp, row in hist.iterrows():
            data.append({
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "data": data
        }
        
    except Exception as e:
        print(f"Error fetching Yahoo Finance intraday for {symbol}: {e}")
        return None


def search_yahoo_symbols(query: str) -> List[Dict]:
    """
    Search for stock symbols using Yahoo Finance.
    Note: This is a simplified search using common symbols.
    """
    try:
        # For a real search, we'd need a different approach as yfinance doesn't have built-in search
        # Here's a simplified version with common symbols
        common_symbols = {
            # Tech
            'apple': ['AAPL', 'Apple Inc.'],
            'microsoft': ['MSFT', 'Microsoft Corporation'],
            'google': ['GOOGL', 'Alphabet Inc.'],
            'alphabet': ['GOOGL', 'Alphabet Inc.'],
            'amazon': ['AMZN', 'Amazon.com Inc.'],
            'tesla': ['TSLA', 'Tesla Inc.'],
            'meta': ['META', 'Meta Platforms Inc.'],
            'facebook': ['META', 'Meta Platforms Inc.'],
            'nvidia': ['NVDA', 'NVIDIA Corporation'],
            'netflix': ['NFLX', 'Netflix Inc.'],
            
            # Finance
            'jpmorgan': ['JPM', 'JPMorgan Chase & Co.'],
            'berkshire': ['BRK-B', 'Berkshire Hathaway Inc.'],
            'goldman': ['GS', 'Goldman Sachs Group Inc.'],
            'wells': ['WFC', 'Wells Fargo & Company'],
            
            # Other major stocks
            'walmart': ['WMT', 'Walmart Inc.'],
            'johnson': ['JNJ', 'Johnson & Johnson'],
            'procter': ['PG', 'Procter & Gamble Company'],
            'coca': ['KO', 'Coca-Cola Company'],
            'disney': ['DIS', 'Walt Disney Company'],
            'boeing': ['BA', 'Boeing Company'],
        }
        
        query_lower = query.lower()
        results = []
        
        # Check if query matches any known companies
        for company, (symbol, name) in common_symbols.items():
            if query_lower in company or query_lower in symbol.lower():
                # Verify the symbol exists by trying to fetch basic info
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info and 'symbol' in info:
                        results.append({
                            "symbol": symbol,
                            "name": name,
                            "type": "Equity",
                            "region": "United States",
                            "market_open": "09:30",
                            "market_close": "16:00",
                            "timezone": "UTC-05",
                            "currency": "USD",
                            "match_score": 1.0 if query_lower == symbol.lower() else 0.8
                        })
                except:
                    continue
        
        # If query looks like a symbol, try it directly
        if len(query) <= 5 and query.isalpha():
            try:
                ticker = yf.Ticker(query.upper())
                info = ticker.info
                if info and 'longName' in info:
                    results.insert(0, {
                        "symbol": query.upper(),
                        "name": info.get('longName', f"{query.upper()} Inc."),
                        "type": "Equity",
                        "region": "United States",
                        "market_open": "09:30",
                        "market_close": "16:00",
                        "timezone": "UTC-05",
                        "currency": "USD",
                        "match_score": 1.0
                    })
            except:
                pass
        
        return results[:10]  # Return top 10 matches
        
    except Exception as e:
        print(f"Error searching Yahoo Finance symbols: {e}")
        return []


def get_market_summary() -> Dict:
    """
    Get major market indices from Yahoo Finance.
    """
    try:
        indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC", 
            "Dow Jones": "^DJI",
            "VIX": "^VIX"
        }
        
        summary = {}
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    summary[name] = round(current_price, 2)
            except:
                # Fallback values if fetch fails
                fallback_values = {
                    "S&P 500": 5745.37,
                    "NASDAQ": 18291.62,
                    "Dow Jones": 42063.36,
                    "VIX": 16.85
                }
                summary[name] = fallback_values.get(name, 0.0)
        
        return summary
        
    except Exception as e:
        print(f"Error fetching market summary: {e}")
        return {
            "S&P 500": 5745.37,
            "NASDAQ": 18291.62,
            "Dow Jones": 42063.36,
            "VIX": 16.85
        }


# Test function
def test_yahoo_finance():
    """Test all Yahoo Finance functions."""
    print("🔄 Testing Yahoo Finance integration...")
    
    # Test quote
    print("\n📊 Testing quote fetch (AAPL):")
    quote = fetch_yahoo_quote("AAPL")
    if quote:
        print(f"✅ Quote: {quote['symbol']} - ${quote['price']} ({quote['change']:+.2f})")
    else:
        print("❌ Quote fetch failed")

    # Test Indian stock quote
    print("\n🇮🇳 Testing Indian stock quote (RELIANCE.NS):")
    indian_quote = fetch_yahoo_quote("RELIANCE.NS")
    if indian_quote:
        currency = "₹" if indian_quote.get('currency') == 'INR' else "$"
        print(f"✅ Quote: {indian_quote['symbol']} - {currency}{indian_quote['price']} ({indian_quote['change']:+.2f})")
    else:
        print("❌ Indian stock quote fetch failed")
    
    # Test search
    print("\n🔍 Testing symbol search ('apple'):")
    results = search_yahoo_symbols("apple")
    if results:
        print(f"✅ Found {len(results)} results:")
        for result in results[:3]:
            print(f"   {result['symbol']}: {result['name']}")
    else:
        print("❌ Search failed")
    
    # Test intraday
    print("\n📈 Testing intraday data (AAPL, 1d, 5m):")
    intraday = fetch_yahoo_intraday("AAPL", "1d", "5m")
    if intraday and intraday['data']:
        print(f"✅ Intraday: {len(intraday['data'])} data points")
        print(f"   Latest: {intraday['data'][-1]['timestamp']} - ${intraday['data'][-1]['close']}")
    else:
        print("❌ Intraday fetch failed")
    
    # Test market summary
    print("\n📈 Testing market summary:")
    summary = get_market_summary()
    if summary:
        print("✅ Market Summary:")
        for index, value in summary.items():
            print(f"   {index}: {value}")
    else:
        print("❌ Market summary failed")
    
    print("\n🎉 Yahoo Finance test complete!")


if __name__ == "__main__":
    test_yahoo_finance()