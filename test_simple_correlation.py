#!/usr/bin/env python3
"""
Simple test of the new correlation function
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

import yfinance as yf
import pandas as pd
import numpy as np

def test_simple_correlation():
    """Test the simplified correlation function"""
    print("🔄 Testing simplified correlation function...")
    
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    try:
        # Test individual symbol fetch
        price_data = {}
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if not hist.empty and 'Close' in hist.columns:
                price_data[symbol] = hist['Close']
                print(f"✅ {symbol}: {len(hist)} days of data")
            else:
                print(f"❌ {symbol}: No data")
        
        if len(price_data) >= 2:
            # Create DataFrame
            df = pd.DataFrame(price_data)
            print(f"✅ Combined data shape: {df.shape}")
            
            # Calculate returns and correlation
            returns = df.pct_change().dropna()
            corr = returns.corr()
            
            print(f"✅ Correlation matrix:\n{corr.round(3)}")
            return True
        else:
            print("❌ Not enough data")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_correlation()
    if success:
        print("\n🎉 Simple correlation function works!")
    else:
        print("\n❌ Simple correlation function failed!")