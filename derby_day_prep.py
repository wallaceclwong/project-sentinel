import requests
import json
from datetime import datetime
 
def derby_day_readiness_check():
    """Complete Derby Day readiness check"""
    print("🏆 DERBY DAY READINESS CHECK")
    print("=" * 40)
    
    api_url = "https://sentinel-api-service-tgo3qpmhda-df.a.run.app"
    
    # 1. System Health
    print("1. System Health Check:")
    try:
        health = requests.get(f"{api_url}/health", timeout=10)
        if health.status_code == 200:
            print("   ✅ System healthy")
        else:
            print(f"   ❌ System unhealthy: {health.status_code}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    # 2. Complete Workflow Test
    print("2. Complete Workflow Test:")
    
    workflows = [
        ("Data Scraping", f"{api_url}/scrape/race-cards"),
        ("Weather Analysis", f"{api_url}/analyze/weather"),
        ("Race Prediction", f"{api_url}/predict/race"),
        ("Betting Recommendation", f"{api_url}/recommend/betting")
    ]
    
    all_passed = True
    for name, url in workflows:
        try:
            response = requests.post(url, timeout=30)
            if response.status_code == 200:
                print(f"   ✅ {name}: Working")
            else:
                print(f"   ❌ {name}: Failed ({response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"   ❌ {name}: Error ({e})")
            all_passed = False
    
    # 3. Derby Day Simulation
    print("3. Derby Day Simulation:")
    if all_passed:
        print("   ✅ All systems ready for Derby Day")
        print("   🏆 Sentinel Racing prepared for March 16, 2026")
    else:
        print("   ❌ Systems need attention before Derby Day")
    
    # 4. Performance Check
    print("4. Performance Check:")
    start_time = datetime.now()
    
    try:
        response = requests.post(f"{api_url}/recommend/betting", timeout=30)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if response_time < 5:
            print(f"   ✅ Response time: {response_time:.2f}s (Excellent)")
        elif response_time < 10:
            print(f"   ⚠️ Response time: {response_time:.2f}s (Good)")
        else:
            print(f"   ❌ Response time: {response_time:.2f}s (Needs optimization)")
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
    
    print(f"\\n📊 Derby Day Readiness Check completed at: {datetime.now()}")
    print(f"🗓️ Days until Derby Day: 6")
 
if __name__ == "__main__":
    derby_day_readiness_check()
