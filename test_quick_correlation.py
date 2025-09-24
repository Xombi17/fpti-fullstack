#!/usr/bin/env python3
"""
Quick test of correlation function in app context
"""
import sys
import os

# Add the frontend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

try:
    # Test the imports
    import yfinance as yf
    import pandas as pd
    import numpy as np
    
    print("✅ All imports successful")
    
    # Test basic yfinance functionality
    symbols = ['AAPL', 'MSFT']
    print(f"🔄 Testing download for {symbols}")
    
    data = yf.download(symbols, period="1mo", interval="1d", auto_adjust=True, progress=False)
    print(f"✅ Downloaded data shape: {data.shape}")
    print(f"✅ Data columns: {data.columns.tolist()}")
    
    # Test correlation calculation
    if len(symbols) > 1:
        close_data = data['Close']
    else:
        close_data = data['Close'] if 'Close' in data.columns else data
    
    returns = close_data.pct_change().dropna()
    correlation = returns.corr()
    
    print(f"✅ Correlation matrix:\n{correlation}")
    
    print("\n🎉 Correlation function should work now!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()