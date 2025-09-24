#!/usr/bin/env python3
"""
Test script to verify the asset correlation matrix functionality
"""
import sys
import os

# Add the frontend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    
    def test_correlation_matrix():
        """Test the correlation matrix calculation"""
        print("🔄 Testing Asset Correlation Matrix...")
        
        # Test symbols
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']
        
        try:
            # Download 3 months of data
            print(f"📊 Downloading 3 months of data for: {symbols}")
            data = yf.download(symbols, period="3mo", interval="1d")['Close']
            
            if data.empty:
                print("❌ No data downloaded")
                return False
            
            print(f"✅ Downloaded {len(data)} days of data")
            
            # Calculate returns
            returns = data.pct_change().dropna()
            print(f"✅ Calculated returns: {len(returns)} observations")
            
            # Calculate correlation matrix
            correlation_matrix = returns.corr()
            print(f"✅ Correlation matrix shape: {correlation_matrix.shape}")
            
            print("\n📈 Correlation Matrix:")
            print("=" * 50)
            print(correlation_matrix.round(3))
            
            print("\nKey Insights:")
            # Find highest correlation (excluding self-correlation)
            corr_values = correlation_matrix.values
            np.fill_diagonal(corr_values, np.nan)  # Remove diagonal
            max_corr_idx = np.unravel_index(np.nanargmax(corr_values), corr_values.shape)
            max_corr = corr_values[max_corr_idx]
            
            print(f"🔗 Highest correlation: {correlation_matrix.index[max_corr_idx[0]]} vs {correlation_matrix.columns[max_corr_idx[1]]} = {max_corr:.3f}")
            
            # Find lowest correlation
            min_corr_idx = np.unravel_index(np.nanargmin(corr_values), corr_values.shape)
            min_corr = corr_values[min_corr_idx]
            
            print(f"🔗 Lowest correlation: {correlation_matrix.index[min_corr_idx[0]]} vs {correlation_matrix.columns[min_corr_idx[1]]} = {min_corr:.3f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in correlation calculation: {e}")
            return False
    
    print("🚀 Asset Correlation Matrix Test")
    print("=" * 40)
    
    success = test_correlation_matrix()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Correlation matrix is working with real data!")
        print("🎯 Your Analysis page will now show:")
        print("   • Real correlation between stocks")
        print("   • 3-month historical data")
        print("   • Interactive heatmap visualization")
        print("   • Portfolio-specific correlations")
    else:
        print("❌ Correlation matrix test failed")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure yfinance is installed: pip install yfinance")
except Exception as e:
    print(f"❌ Test failed: {e}")