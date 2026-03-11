import requests
import time
import statistics
from datetime import datetime
 
class PerformanceAnalyzer:
    def __init__(self):
        self.api_url = "https://sentinel-api-service-tgo3qpmhda-df.a.run.app"
        self.results = {}
    
    def test_endpoint(self, name, url, method="GET", iterations=5):
        """Test endpoint performance"""
        print(f"Testing {name}...")
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                if method == "GET":
                    response = requests.get(url, timeout=30)
                else:
                    response = requests.post(url, timeout=30)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    success_count += 1
                else:
                    print(f"  Failed: Status {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        if response_times:
            self.results[name] = {
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'success_rate': success_count / iterations,
                'total_tests': iterations
            }
            
            print(f"  ✅ Avg: {self.results[name]['avg_response_time']:.2f}s")
            print(f"  ✅ Success Rate: {self.results[name]['success_rate']*100:.1f}%")
        else:
            self.results[name] = {
                'avg_response_time': 0,
                'success_rate': 0,
                'total_tests': iterations
            }
            print(f"  ❌ All tests failed")
    
    def run_performance_tests(self):
        """Run comprehensive performance tests"""
        print("🚀 SENTINEL-RACING PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        # Test all endpoints
        endpoints = [
            ("Health Check", f"{self.api_url}/health", "GET"),
            ("System Status", f"{self.api_url}/system/status", "GET"),
            ("Data Scraping", f"{self.api_url}/scrape/race-cards", "POST"),
            ("Weather Analysis", f"{self.api_url}/analyze/weather", "POST"),
            ("Race Prediction", f"{self.api_url}/predict/race", "POST"),
            ("Betting Recommendation", f"{self.api_url}/recommend/betting", "POST")
        ]
        
        for name, url, method in endpoints:
            self.test_endpoint(name, url, method)
            print()
        
        self.generate_report()
    
    def generate_report(self):
        """Generate performance report"""
        print("📊 PERFORMANCE REPORT")
        print("=" * 30)
        
        overall_performance = "Excellent"
        slow_endpoints = []
        
        for name, results in self.results.items():
            avg_time = results['avg_response_time']
            success_rate = results['success_rate']
            
            if avg_time > 5:
                slow_endpoints.append(name)
                overall_performance = "Needs Optimization"
            elif avg_time > 2 and overall_performance == "Excellent":
                overall_performance = "Good"
            
            if success_rate < 0.9:
                overall_performance = "Needs Attention"
        
        print(f"Overall Performance: {overall_performance}")
        
        if slow_endpoints:
            print(f"Slow endpoints: {', '.join(slow_endpoints)}")
        
        print(f"\nDetailed Results:")
        for name, results in self.results.items():
            print(f"  {name}:")
            print(f"    Response Time: {results['avg_response_time']:.2f}s")
            print(f"    Success Rate: {results['success_rate']*100:.1f}%")
        
        print(f"\nAnalysis completed at: {datetime.now()}")
 
if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    analyzer.run_performance_tests()
