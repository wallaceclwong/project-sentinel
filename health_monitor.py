
import requests
import time
from datetime import datetime
 
def continuous_health_check():
    """Continuous health monitoring"""
    api_url = "https://sentinel-api-service-tgo3qpmhda-df.a.run.app"
    
    while True:
        try:
            health = requests.get(f"{api_url}/health", timeout=10)
            
            if health.status_code == 200:
                print(f"✅ {datetime.now()}: System healthy")
            else:
                print(f"❌ {datetime.now()}: System unhealthy (Status: {health.status_code})")
                
        except Exception as e:
            print(f"❌ {datetime.now()}: Health check failed: {e}")
        
        time.sleep(60)  # Check every minute
 
if __name__ == "__main__":
    print("🔍 Starting continuous health monitoring...")
    continuous_health_check()
