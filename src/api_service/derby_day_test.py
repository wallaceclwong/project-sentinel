import requests
import json
from datetime import datetime
 
API_URL = "https://sentinel-api-service-xxxxxxxxx-ew.a.run.app"  # Update with actual URL
 
def test_derby_day_scenario():
    """Test complete Derby Day scenario"""
    print("🏆 DERBY DAY SCENARIO TEST")
    print("=" * 50)
    
    # 1. System Health Check
    print("\n1. System Health Check:")
    health = requests.get(f"{API_URL}/health")
    print(f"   Status: {health.status_code}")
    print(f"   Response: {health.json()}")
    
    # 2. Complete System Status
    print("\n2. Complete System Status:")
    status = requests.get(f"{API_URL}/system/status")
    print(f"   Status: {status.status_code}")
    print(f"   Response: {json.dumps(status.json(), indent=2)}")
    
    # 3. Scrape Today's Race Data
    print("\n3. Scraping Race Data:")
    scrape = requests.post(f"{API_URL}/scrape/race-cards")
    print(f"   Status: {scrape.status_code}")
    print(f"   Data: {json.dumps(scrape.json(), indent=2)}")
    
    # 4. Weather Analysis
    print("\n4. Weather Analysis:")
    weather = requests.post(f"{API_URL}/analyze/weather")
    print(f"   Status: {weather.status_code}")
    print(f"   Analysis: {json.dumps(weather.json(), indent=2)}")
    
    # 5. Race Prediction
    print("\n5. Race Prediction:")
    prediction = requests.post(f"{API_URL/predict/race}")
    print(f"   Status: {prediction.status_code}")
    print(f"   Prediction: {json.dumps(prediction.json(), indent=2)}")
    
    # 6. Betting Recommendation
    print("\n6. Betting Recommendation:")
    betting = requests.post(f"{API_URL}/recommend/betting")
    print(f"   Status: {betting.status_code}")
    print(f"   Recommendation: {json.dumps(betting.json(), indent=2)}")
    
    print("\n" + "=" * 50)
    print("🎯 DERBY DAY SCENARIO TEST COMPLETE")
    print(f"⏰ Test completed at: {datetime.now()}")
 
if __name__ == "__main__":
    test_derby_day_scenario()
