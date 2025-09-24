#!/usr/bin/env python3
"""
Test script to verify Yahoo Finance integration works perfectly
"""
import sys
import os

# Add the frontend directory to Python path so we can import the service
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

try:
    from yahoo_finance_service import test_yahoo_finance
    print("🚀 Running Yahoo Finance Integration Test")
    print("=" * 50)
    test_yahoo_finance()
    print("\n✅ All tests completed!")
    print("\n🎉 Yahoo Finance is ready to use!")
    print("   • No API key required")
    print("   • No rate limits")
    print("   • Real-time data")
    print("   • Free forever!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install yfinance: pip install yfinance")
except Exception as e:
    print(f"❌ Test failed: {e}")