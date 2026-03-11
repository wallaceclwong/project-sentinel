
import requests
import time
from datetime import datetime
 
def performance_test():
    """Test system performance"""
    api_url = "https://sentinel-api-service-tgo3qpmhda-df.a.run.app"
    
    tests = [
        ("Health Check", f"{api_url}/health"),
        ("System Status", f"{api_url}/system/status"),
        ("Weather Analysis", f"{api_url}/analyze/weather"),
        ("Race Prediction", f"{api_url}/predict/race"),
        ("Betting Recommendation", f"{api_url}/recommend/betting")
    ]
    
    results = {}
    
    for test_name, url in tests:
        start_time = time.time()
        try:
            if "health" in url or "status" in url:
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, timeout=30)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            results[test_name] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            }
        except Exception as e:
            results[test_name] = {
                "status_code": 0,
                "response_time": 0,
                "success": False,
                "error": str(e)
            }
    
    return results
 
if __name__ == "__main__":
    print("🚀 PERFORMANCE TEST")
    print("=" * 30)
    results = performance_test()
    
    for test, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {test}: {result['response_time']:.2f}s")
    
    print(f"\n📊 Test completed at: {datetime.now()}")
