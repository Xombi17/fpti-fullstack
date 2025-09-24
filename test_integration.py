"""
Test script to verify API endpoints and functionality.
"""
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test all API endpoints."""
    print("Testing FPTI API Endpoints")
    print("=" * 40)
    
    # Test root endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✓ Root endpoint: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
    
    # Test health check
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✓ Health check: {response.status_code}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
    
    # Test portfolios
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/portfolios/")
        print(f"✓ Get portfolios: {response.status_code}")
        if response.status_code == 200:
            portfolios = response.json()
            print(f"  Found {len(portfolios)} portfolios")
            
            # Test getting specific portfolio
            if portfolios:
                portfolio_id = portfolios[0]["id"]
                response = requests.get(f"{API_BASE_URL}/api/v1/portfolios/{portfolio_id}")
                print(f"✓ Get portfolio {portfolio_id}: {response.status_code}")
                
                # Test portfolio value
                response = requests.get(f"{API_BASE_URL}/api/v1/portfolios/{portfolio_id}/value")
                print(f"✓ Get portfolio value: {response.status_code}")
                if response.status_code == 200:
                    value_data = response.json()
                    print(f"  Portfolio value: ${value_data.get('total_value', 0):,.2f}")
                
                # Test portfolio allocation
                response = requests.get(f"{API_BASE_URL}/api/v1/portfolios/{portfolio_id}/allocation")
                print(f"✓ Get portfolio allocation: {response.status_code}")
    except Exception as e:
        print(f"✗ Portfolio endpoints failed: {e}")
    
    # Test assets
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/assets/")
        print(f"✓ Get assets: {response.status_code}")
        if response.status_code == 200:
            assets = response.json()
            print(f"  Found {len(assets)} assets")
    except Exception as e:
        print(f"✗ Asset endpoints failed: {e}")
    
    # Test transactions
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/transactions/")
        print(f"✓ Get transactions: {response.status_code}")
        if response.status_code == 200:
            transactions = response.json()
            print(f"  Found {len(transactions)} transactions")
    except Exception as e:
        print(f"✗ Transaction endpoints failed: {e}")
    
    # Test market data
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/market-data/summary")
        print(f"✓ Get market summary: {response.status_code}")
        
        # Test individual stock price (may fail without real API keys)
        response = requests.get(f"{API_BASE_URL}/api/v1/market-data/price/AAPL")
        print(f"✓ Get AAPL price: {response.status_code}")
        if response.status_code == 200:
            price_data = response.json()
            print(f"  AAPL price: ${price_data.get('price', 0):.2f}")
    except Exception as e:
        print(f"✗ Market data endpoints failed: {e}")
    
    # Test analytics
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/analytics/portfolio/1/performance")
        print(f"✓ Get portfolio performance: {response.status_code}")
        
        # Test Monte Carlo simulation
        mc_payload = {
            "target_value": 1000000,
            "years": 10,
            "monthly_contribution": 1000,
            "num_simulations": 100
        }
        response = requests.post(f"{API_BASE_URL}/api/v1/analytics/portfolio/1/monte-carlo", 
                               json=mc_payload)
        print(f"✓ Monte Carlo simulation: {response.status_code}")
        if response.status_code == 200:
            mc_data = response.json()
            print(f"  Success probability: {mc_data.get('success_probability', 0):.1%}")
    except Exception as e:
        print(f"✗ Analytics endpoints failed: {e}")

def test_frontend_connectivity():
    """Test if frontend can connect to backend."""
    print("\nTesting Frontend Connectivity")
    print("=" * 40)
    
    try:
        import dash
        print("✓ Dash is available")
        
        # Test API connectivity from frontend perspective
        response = requests.get(f"{API_BASE_URL}/api/v1/portfolios/")
        if response.status_code == 200:
            print("✓ Frontend can connect to backend API")
        else:
            print(f"✗ Frontend connection failed: {response.status_code}")
            
    except ImportError:
        print("✗ Dash not installed")
    except Exception as e:
        print(f"✗ Frontend connectivity test failed: {e}")

def create_test_transaction():
    """Create a test transaction via API."""
    print("\nCreating Test Transaction")
    print("=" * 40)
    
    try:
        # First, get available portfolios and assets
        portfolios_response = requests.get(f"{API_BASE_URL}/api/v1/portfolios/")
        assets_response = requests.get(f"{API_BASE_URL}/api/v1/assets/")
        
        if portfolios_response.status_code == 200 and assets_response.status_code == 200:
            portfolios = portfolios_response.json()
            assets = assets_response.json()
            
            if portfolios and assets:
                # Create a test transaction
                transaction_data = {
                    "portfolio_id": portfolios[0]["id"],
                    "asset_id": assets[0]["id"],
                    "transaction_type": "buy",
                    "quantity": 10,
                    "price": 150.00,
                    "total_amount": 1500.00,
                    "fees": 9.99,
                    "currency": "USD",
                    "transaction_date": datetime.now().isoformat(),
                    "description": "Test transaction via API"
                }
                
                response = requests.post(f"{API_BASE_URL}/api/v1/transactions/", 
                                       json=transaction_data)
                print(f"✓ Create transaction: {response.status_code}")
                
                if response.status_code == 200:
                    transaction = response.json()
                    print(f"  Created transaction ID: {transaction['id']}")
                else:
                    print(f"  Error: {response.text}")
            else:
                print("✗ No portfolios or assets available for test transaction")
        else:
            print("✗ Could not fetch portfolios and assets")
            
    except Exception as e:
        print(f"✗ Test transaction creation failed: {e}")

def run_all_tests():
    """Run all tests."""
    print("FPTI Full-Stack Dashboard Test Suite")
    print("=" * 50)
    
    test_api_endpoints()
    test_frontend_connectivity()
    create_test_transaction()
    
    print("\n" + "=" * 50)
    print("Test Suite Complete!")
    print("\nTo start the application:")
    print("1. Backend: cd backend && python main.py")
    print("2. Frontend: cd frontend && python app.py")
    print("3. Visit: http://localhost:8050")

if __name__ == "__main__":
    run_all_tests()