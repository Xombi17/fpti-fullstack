#!/usr/bin/env python3
"""
Test the correlation matrix callback directly
"""
import sys
import os

# Add the frontend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

# Import what we need
import yfinance as yf
import pandas as pd
import numpy as np

def test_correlation_callback():
    """Test the exact same logic as in the callback"""
    print("🔄 Testing correlation matrix callback logic...")
    
    try:
        # Same logic as in the callback
        assets = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        print(f"DEBUG: Calculating correlation matrix for: {assets}")
        
        # Test the fetch function logic
        print(f"DEBUG: Starting correlation fetch for {assets}")
        
        # Use the same approach as in the app
        price_data = {}
        for symbol in assets:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1mo")
                if not hist.empty and 'Close' in hist.columns:
                    price_data[symbol] = hist['Close']
                    print(f"DEBUG: Successfully fetched {symbol}: {len(hist)} days")
                else:
                    print(f"DEBUG: No data for {symbol}")
            except Exception as e:
                print(f"DEBUG: Error fetching {symbol}: {e}")
                continue
        
        print(f"DEBUG: Collected data for {len(price_data)} symbols")
        
        if len(price_data) < 2:
            print("DEBUG: Not enough symbols with data, using mock data")
            raise ValueError("Insufficient data for correlation")
        
        # Create DataFrame from individual symbol data
        df = pd.DataFrame(price_data)
        print(f"DEBUG: Combined DataFrame shape: {df.shape}")
        
        # Calculate returns
        returns = df.pct_change().dropna()
        print(f"DEBUG: Returns shape: {returns.shape}")
        
        if returns.empty or len(returns) < 5:
            raise ValueError("Not enough return data for correlation")
        
        # Calculate correlation
        corr_matrix = returns.corr()
        print(f"DEBUG: Correlation matrix shape: {corr_matrix.shape}")
        
        # Fill any NaN values
        corr_matrix = corr_matrix.fillna(0)
        for i in range(len(corr_matrix)):
            corr_matrix.iloc[i, i] = 1.0
        
        print(f"✅ Correlation Matrix:")
        print(corr_matrix.round(3))
        
        return True
        
    except Exception as e:
        print(f"❌ Error in correlation test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Correlation Matrix Callback")
    print("=" * 50)
    
    success = test_correlation_callback()
    
    if success:
        print("\n✅ Correlation logic works - issue might be in Dash callback")
    else:
        print("\n❌ Correlation logic failed")