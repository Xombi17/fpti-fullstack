"""
Quick test for the market data functions
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

from datetime import datetime
import requests

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY = "5DX20ZGQJBILGF2S"

def test_quote_function():
    """Test the quote function"""
    print("Testing Alpha Vantage quote function...")
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": "AAPL",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                print("✅ Quote data received!")
                print(f"Symbol: {quote.get('01. symbol', 'N/A')}")
                print(f"Price: ${quote.get('05. price', 'N/A')}")
                print(f"Change: {quote.get('09. change', 'N/A')}")
            else:
                print("❌ No Global Quote in response")
                print(f"Full response: {data}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quote_function()