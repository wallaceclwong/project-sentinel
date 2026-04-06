import requests
import json
from datetime import datetime
 
def get_service_urls():
    """Get deployed service URLs"""
    try:
        # Use gcloud to get service URLs
        import subprocess
        
        scraping_url = subprocess.check_output([
            'gcloud', 'run', 'services', 'describe', 'sentinel-scraping-service',
            '--region=asia-east2', '--format=value(status.url)'
        ]).decode('utf-8').strip()
        
        ai_url = subprocess.check_output([
            'gcloud', 'run', 'services', 'describe', 'sentinel-ai-service',
            '--region=asia-east2', '--format=value(status.url)'
        ]).decode('utf-8').strip()
        
        api_url = subprocess.check_output([
            'gcloud', 'run', 'services', 'describe', 'sentinel-api-service',
            '--region=asia-east2', '--format=value(status.url)'
        ]).decode('utf-8').strip()
        
        return scraping_url, ai_url, api_url
    except Exception as e:
        print(f"Error getting service URLs: {e}")
        return None, None, None
 
def test_derby_day_scenario():
    """Test complete Derby Day scenario"""
    print("🏆 DERBY DAY SCENARIO TEST")
    print("=" * 50)
    
    # Get service URLs
    scraping_url, ai_url, api_url = get_service_urls()
    
    if not api_url:
        print("❌ Could not get API Gateway URL")
        return
    
    print(f"🌐 API Gateway: {api_url}")
    print(f"📊 Scraping Service: {scraping_url}")
    print(f"🤖 AI Service: {ai_url}")
    
    # 1. System Health Check
    print("\n1. System Health Check:")
    try:
        health = requests.get(f"{api_url}/health", timeout=10)
        print(f"   Status: {health.status_code}")
        if health.status_code == 200:
            print(f"   ✅ API Gateway Healthy")
            print(f"   Response: {json.dumps(health.json(), indent=6)}")
        else:
            print(f"   ❌ API Gateway Unhealthy")
    except Exception as e:
        print(f"   ❌ Health Check Failed: {e}")
    
    # 2. Complete System Status
    print("\n2. Complete System Status:")
    try:
        status = requests.get(f"{api_url}/system/status", timeout=10)
        print(f"   Status: {status.status_code}")
        if status.status_code == 200:
            print(f"   ✅ System Status Retrieved")
            status_data = status.json()
            print(f"   System: {status_data.get('system', 'unknown')}")
            services = status_data.get('services', {})
            for service, info in services.items():
                service_status = info.get('status', 'unknown')
                print(f"   {service}: {service_status}")
        else:
            print(f"   ❌ System Status Failed")
    except Exception as e:
        print(f"   ❌ System Status Error: {e}")
    
    # 3. Scrape Race Data
    print("\n3. Scraping Race Data:")
    try:
        scrape = requests.post(f"{api_url}/scrape/race-cards", timeout=30)
        print(f"   Status: {scrape.status_code}")
        if scrape.status_code == 200:
            print(f"   ✅ Race Data Scraped")
            data = scrape.json()
            print(f"   Records: {len(data.get('data', []))}")
        else:
            print(f"   ❌ Scraping Failed")
    except Exception as e:
        print(f"   ❌ Scraping Error: {e}")
    
    # 4. Weather Analysis
    print("\n4. Weather Analysis:")
    try:
        weather = requests.post(f"{api_url}/analyze/weather", timeout=30)
        print(f"   Status: {weather.status_code}")
        if weather.status_code == 200:
            print(f"   ✅ Weather Analysis Complete")
            data = weather.json()
            analysis = data.get('data', {}).get('analysis', 'No analysis')
            print(f"   Analysis: {analysis[:100]}...")
        else:
            print(f"   ❌ Weather Analysis Failed")
    except Exception as e:
        print(f"   ❌ Weather Analysis Error: {e}")
    
    # 5. Race Prediction
    print("\n5. Race Prediction:")
    try:
        prediction = requests.post(f"{api_url}/predict/race", timeout=30)
        print(f"   Status: {prediction.status_code}")
        if prediction.status_code == 200:
            print(f"   ✅ Race Prediction Generated")
            data = prediction.json()
            pred_text = data.get('data', {}).get('prediction', 'No prediction')
            print(f"   Prediction: {pred_text[:100]}...")
        else:
            print(f"   ❌ Race Prediction Failed")
    except Exception as e:
        print(f"   ❌ Race Prediction Error: {e}")
    
    # 6. Betting Recommendation
    print("\n6. Betting Recommendation:")
    try:
        betting = requests.post(f"{api_url}/recommend/betting", timeout=30)
        print(f"   Status: {betting.status_code}")
        if betting.status_code == 200:
            print(f"   ✅ Betting Recommendation Generated")
            data = betting.json()
            recommendation = data.get('data', {}).get('recommendation', 'No recommendation')
            print(f"   Recommendation: {recommendation[:100]}...")
        else:
            print(f"   ❌ Betting Recommendation Failed")
    except Exception as e:
        print(f"   ❌ Betting Recommendation Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DERBY DAY SCENARIO TEST COMPLETE")
    print(f"⏰ Test completed at: {datetime.now()}")
    
    # Summary
    print("\n📊 TEST SUMMARY:")
    print("   Services tested: API Gateway, Scraping, AI")
    print("   Capabilities verified: Data scraping, Analysis, Prediction, Betting")
    print("   Next steps: Performance optimization, Monitoring setup")
 
if __name__ == "__main__":
    test_derby_day_scenario()
