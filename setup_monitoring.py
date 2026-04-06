import subprocess
import json
 
def setup_cloud_monitoring():
    """Set up Cloud Monitoring for Sentinel Racing"""
    print("📊 SETTING UP CLOUD MONITORING")
    print("=" * 35)
    
    monitoring_setup = {
        "dashboard": {
            "name": "Sentinel Racing Dashboard",
            "metrics": [
                "Cloud Run request latency",
                "Cloud Run request count",
                "Cloud Run error rate",
                "BigQuery query count",
                "Memory usage"
            ]
        },
        "alerts": [
            {
                "name": "High Response Time",
                "condition": "Response time > 5 seconds",
                "threshold": "5s"
            },
            {
                "name": "High Error Rate", 
                "condition": "Error rate > 10%",
                "threshold": "10%"
            },
            {
                "name": "Service Down",
                "condition": "Health check fails",
                "threshold": "0% success rate"
            }
        ]
    }
    
    print("Monitoring Dashboard Configuration:")
    for metric in monitoring_setup["dashboard"]["metrics"]:
        print(f"  - {metric}")
    
    print("\nAlert Policies:")
    for alert in monitoring_setup["alerts"]:
        print(f"  - {alert['name']}: {alert['condition']}")
    
    print("\n✅ Monitoring configuration ready")
    print("Set up manually in Cloud Console or use gcloud monitoring commands")
 
def create_health_monitor():
    """Create health monitoring script"""
    health_script = '''
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
'''
    
    with open('health_monitor.py', 'w') as f:
        f.write(health_script)
    
    print("✅ Health monitoring script created")
 
if __name__ == "__main__":
    setup_cloud_monitoring()
    create_health_monitor()
