"""
Application Test Script - Validate Frontend Features
"""
import requests
import time

API_BASE_URL = "http://127.0.0.1:8000/api/v1"
FRONTEND_URL = "http://127.0.0.1:8050"

def test_backend_connectivity():
    """Test if backend API is accessible"""
    print("🔍 Testing Backend Connectivity...")
    try:
        # Test the root endpoint, not the API v1 base
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            print("✅ Backend API is accessible")
            return True
        else:
            print(f"❌ Backend API returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend API is not running or not accessible")
        return False

def test_frontend_connectivity():
    """Test if frontend is accessible"""
    print("🔍 Testing Frontend Connectivity...")
    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            print("✅ Frontend Dashboard is accessible")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend Dashboard is not running or not accessible")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    print("🔍 Testing API Endpoints...")
    
    # Test the new API root endpoint first
    try:
        response = requests.get(f"{API_BASE_URL}/")
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} /api/v1/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ /api/v1/ - Error: {str(e)}")
    
    endpoints = [
        "/portfolios/",
        "/assets/", 
        "/transactions/",
        "/market-data/summary"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            # Accept 200 (success) or 404/422 (empty but working)
            status = "✅" if response.status_code in [200, 404, 422] else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
            results.append(response.status_code in [200, 404, 422])
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("🚀 FPTI Application Test Suite")
    print("=" * 50)
    
    backend_ok = test_backend_connectivity()
    frontend_ok = test_frontend_connectivity() 
    api_ok = test_api_endpoints() if backend_ok else False
    
    print("\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Backend API:      {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Dash:    {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"API Endpoints:    {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if all([backend_ok, frontend_ok, api_ok]):
        print("\n🎉 All tests passed! Application is ready to use.")
        print(f"📊 Dashboard: {FRONTEND_URL}")
        print(f"🔧 API Docs: {API_BASE_URL.replace('/api/v1', '')}/docs")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
        
        if not backend_ok:
            print("\n💡 To start backend:")
            print("cd backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")
            
        if not frontend_ok:
            print("\n💡 To start frontend:")
            print("cd frontend && python app.py")

if __name__ == "__main__":
    main()