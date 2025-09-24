"""
Test script for Alpha Vantage integration
"""
import asyncio
import aiohttp
import sys
import os
from datetime import datetime

# Add the backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.market_data import MarketDataService
from backend.app.core.config import settings

async def test_alpha_vantage():
    """Test Alpha Vantage API integration."""
    print("Testing Alpha Vantage Integration...")
    print(f"API Key configured: {'Yes' if settings.alpha_vantage_api_key else 'No'}")
    print(f"Market data provider: {settings.market_data_provider}")
    print("-" * 50)
    
    async with MarketDataService() as service:
        # Test 1: Get current price
        print("Test 1: Getting current price for AAPL...")
        try:
            price = await service.get_current_price("AAPL")
            print(f"✅ AAPL current price: ${price:.2f}" if price else "❌ Failed to get price")
        except Exception as e:
            print(f"❌ Error getting price: {e}")
        
        print()
        
        # Test 2: Get detailed quote
        print("Test 2: Getting detailed quote for AAPL...")
        try:
            quote = await service.get_alpha_vantage_quote_detailed("AAPL")
            if quote:
                print(f"✅ AAPL detailed quote:")
                print(f"   Price: ${quote['price']:.2f}")
                print(f"   Change: ${quote['change']:.2f} ({quote['change_percent']}%)")
                print(f"   Volume: {quote['volume']:,}")
                print(f"   High: ${quote['high']:.2f}")
                print(f"   Low: ${quote['low']:.2f}")
            else:
                print("❌ Failed to get detailed quote")
        except Exception as e:
            print(f"❌ Error getting detailed quote: {e}")
        
        print()
        
        # Test 3: Search symbols
        print("Test 3: Searching for 'Apple' symbols...")
        try:
            search_results = await service.search_alpha_vantage_symbols("Apple")
            if search_results:
                print(f"✅ Found {len(search_results)} symbols:")
                for result in search_results[:3]:  # Show top 3
                    print(f"   {result['symbol']} - {result['name']} ({result['match_score']:.1%} match)")
            else:
                print("❌ No search results found")
        except Exception as e:
            print(f"❌ Error searching symbols: {e}")
        
        print()
        
        # Test 4: Get multiple prices
        print("Test 4: Getting prices for multiple symbols...")
        try:
            symbols = ["AAPL", "GOOGL", "MSFT"]
            prices = await service.get_multiple_prices(symbols)
            print(f"✅ Multiple prices:")
            for symbol, price in prices.items():
                if price:
                    print(f"   {symbol}: ${price:.2f}")
                else:
                    print(f"   {symbol}: No data")
        except Exception as e:
            print(f"❌ Error getting multiple prices: {e}")

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ['MARKET_DATA_PROVIDER'] = 'alpha_vantage'
    
    asyncio.run(test_alpha_vantage())
    print("\nTest completed!")