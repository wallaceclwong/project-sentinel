import requests
import json
from datetime import datetime

class DerbyDayOperationalCheck:
    def __init__(self):
        self.api_url = "https://sentinel-api-service-tgo3qpmhda-df.a.run.app"
        self.checklist = {}
    
    def check_service_availability(self):
        """Check all services are available"""
        print("🔍 SERVICE AVAILABILITY CHECK")
        print("=" * 35)
        
        services = [
            ("API Gateway", f"{self.api_url}/health"),
            ("Scraping Service", "https://sentinel-scraping-service-tgo3qpmhda-df.a.run.app/health"),
            ("AI Service", "https://sentinel-ai-service-tgo3qpmhda-df.a.run.app/health")
        ]
        
        for name, url in services:
            try:
                response = requests.get(url, timeout=10)
                status = "✅ AVAILABLE" if response.status_code == 200 else "❌ UNAVAILABLE"
                print(f"{name}: {status}")
                self.checklist[f"{name}_available"] = response.status_code == 200
            except Exception as e:
                print(f"{name}: ❌ ERROR ({e})")
                self.checklist[f"{name}_available"] = False
    
    def check_critical_workflows(self):
        """Check critical Derby Day workflows"""
        print("\n🎯 CRITICAL WORKFLOW CHECK")
        print("=" * 30)
        
        workflows = [
            ("Betting Recommendation", f"{self.api_url}/recommend/betting"),
            ("Race Prediction", f"{self.api_url}/predict/race"),
            ("Weather Analysis", f"{self.api_url}/analyze/weather"),
            ("Data Scraping", f"{self.api_url}/scrape/race-cards")
        ]
        
        for name, url in workflows:
            try:
                response = requests.post(url, timeout=30)
                status = "✅ WORKING" if response.status_code == 200 else "❌ FAILED"
                print(f"{name}: {status}")
                self.checklist[f"{name}_working"] = response.status_code == 200
            except Exception as e:
                print(f"{name}: ❌ ERROR ({e})")
                self.checklist[f"{name}_working"] = False
    
    def check_performance_standards(self):
        """Check performance meets Derby Day standards"""
        print("\n⚡ PERFORMANCE STANDARDS CHECK")
        print("=" * 35)
        
        # Test critical betting recommendation endpoint
        start_time = time.time()
        try:
            response = requests.post(f"{self.api_url}/recommend/betting", timeout=30)
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200 and response_time < 5:
                print(f"Betting Response Time: ✅ {response_time:.2f}s (Excellent)")
                self.checklist["performance_standard"] = True
            elif response.status_code == 200 and response_time < 10:
                print(f"Betting Response Time: ⚠️ {response_time:.2f}s (Good)")
                self.checklist["performance_standard"] = True
            else:
                print(f"Betting Response Time: ❌ {response_time:.2f}s (Needs optimization)")
                self.checklist["performance_standard"] = False
        except Exception as e:
            print(f"Performance Check: ❌ ERROR ({e})")
            self.checklist["performance_standard"] = False
    
    def check_data_integrity(self):
        """Check data pipeline integrity"""
        print("\n🗄️ DATA INTEGRITY CHECK")
        print("=" * 30)
        
        try:
            # Test data scraping and storage
            response = requests.post(f"{self.api_url}/scrape/race-cards", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"Data Pipeline: ✅ WORKING ({len(data)} records)")
                    self.checklist["data_integrity"] = True
                else:
                    print("Data Pipeline: ⚠️ LIMITED DATA")
                    self.checklist["data_integrity"] = False
            else:
                print(f"Data Pipeline: ❌ FAILED (Status: {response.status_code})")
                self.checklist["data_integrity"] = False
        except Exception as e:
            print(f"Data Pipeline: ❌ ERROR ({e})")
            self.checklist["data_integrity"] = False
    
    def generate_derby_day_report(self):
        """Generate comprehensive Derby Day readiness report"""
        print("\n🏆 DERBY DAY OPERATIONAL READINESS REPORT")
        print("=" * 50)
        
        # Calculate readiness score
        total_checks = len(self.checklist)
        passed_checks = sum(1 for check in self.checklist.values() if check)
        readiness_score = (passed_checks / total_checks) * 100
        
        print(f"Readiness Score: {readiness_score:.1f}%")
        print(f"Checks Passed: {passed_checks}/{total_checks}")
        
        # Detailed status
        print(f"\nDetailed Status:")
        for check, status in self.checklist.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check.replace('_', ' ').title()}")
        
        # Overall assessment
        if readiness_score >= 95:
            assessment = "🏆 EXCELLENT - Ready for Derby Day"
        elif readiness_score >= 85:
            assessment = "✅ GOOD - Ready with minor monitoring"
        elif readiness_score >= 70:
            assessment = "⚠️ NEEDS ATTENTION - Fix issues before Derby Day"
        else:
            assessment = "❌ NOT READY - Significant issues to resolve"
        
        print(f"\nOverall Assessment: {assessment}")
        
        # Derby Day countdown
        derby_day = datetime(2026, 3, 16)
        days_until = (derby_day - datetime.now()).days
        print(f"\n🗓️ Days until Derby Day: {days_until}")
        
        if days_until <= 7 and readiness_score >= 85:
            print("🎯 TIMELINE: On track for Derby Day success!")
        elif days_until <= 7 and readiness_score < 85:
            print("⚠️ TIMELINE: Urgent fixes needed for Derby Day!")
        else:
            print("🚀 TIMELINE: Good preparation timeline")
        
        print(f"\nReport generated at: {datetime.now()}")

if __name__ == "__main__":
    import time
    
    checker = DerbyDayOperationalCheck()
    
    print("🏆 DERBY DAY OPERATIONAL READINESS CHECK")
    print("=" * 50)
    
    checker.check_service_availability()
    checker.check_critical_workflows()
    checker.check_performance_standards()
    checker.check_data_integrity()
    checker.generate_derby_day_report()
