#!/usr/bin/env python3
"""
Test script to verify the new Alpha Vantage API key is working
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
print(f"Using API Key: {API_KEY}")

if not API_KEY:
    print("❌ No API key found in environment variables!")
    exit(1)

# Test the API key with a simple quote request
def test_api_key():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": "AAPL",
        "apikey": API_KEY
    }
    
    print("\n🔄 Testing API key with AAPL quote...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n📊 API Response:")
            print(f"Keys in response: {list(data.keys())}")
            
            if "Information" in data:
                print(f"❌ API Error: {data['Information']}")
                return False
            elif "Note" in data:
                print(f"⚠️  API Note: {data['Note']}")
                return False
            elif "Global Quote" in data:
                quote = data["Global Quote"]
                if quote:
                    symbol = quote.get("01. symbol", "N/A")
                    price = quote.get("05. price", "N/A")
                    change = quote.get("09. change", "N/A")
                    print(f"✅ SUCCESS! {symbol}: ${price} (Change: {change})")
                    return True
                else:
                    print("❌ Empty Global Quote data")
                    return False
            else:
                print(f"❌ Unexpected response format: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Alpha Vantage API Key Test")
    print("=" * 40)
    
    success = test_api_key()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ API key is working! You can now restart your frontend.")
    else:
        print("❌ API key test failed. Check your key and try again.")