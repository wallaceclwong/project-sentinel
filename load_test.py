import requests
import time
import threading
from datetime import datetime
import statistics

class DerbyDayLoadTest:
    def __init__(self):
        self.api_url = "https://sentinel-api-service-tgo3qpmhda-df.a.run.app"
        self.results = []
        self.lock = threading.Lock()
    
    def single_user_simulation(self, user_id):
        """Simulate single user during Derby Day"""
        try:
            start_time = time.time()
            
            # 1. Check system health
            health = requests.get(f"{self.api_url}/health", timeout=10)
            
            # 2. Get betting recommendation (most critical)
            betting = requests.post(f"{self.api_url}/recommend/betting", timeout=30)
            
            # 3. Get race prediction
            prediction = requests.post(f"{self.api_url}/predict/race", timeout=30)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            success = (health.status_code == 200 and 
                     betting.status_code == 200 and 
                     prediction.status_code == 200)
            
            with self.lock:
                self.results.append({
                    'user_id': user_id,
                    'response_time': response_time,
                    'success': success,
                    'timestamp': datetime.now()
                })
                
        except Exception as e:
            with self.lock:
                self.results.append({
                    'user_id': user_id,
                    'response_time': 0,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
    
    def run_load_test(self, concurrent_users=10):
        """Run Derby Day load test"""
        print(f"🏆 DERBY DAY LOAD TEST - {concurrent_users} CONCURRENT USERS")
        print("=" * 60)
        
        # Start concurrent users
        threads = []
        start_time = time.time()
        
        for i in range(concurrent_users):
            thread = threading.Thread(target=self.single_user_simulation, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        self.analyze_results(total_time, concurrent_users)
    
    def analyze_results(self, total_time, users):
        """Analyze load test results"""
        print(f"\n📊 LOAD TEST RESULTS")
        print("=" * 30)
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        success_rate = len(successful_requests) / len(self.results) * 100
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        # Calculate throughput
        throughput = len(successful_requests) / total_time if total_time > 0 else 0
        
        print(f"Concurrent Users: {users}")
        print(f"Total Test Time: {total_time:.2f}s")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Avg Response Time: {avg_response_time:.2f}s")
        print(f"Min Response Time: {min_response_time:.2f}s")
        print(f"Max Response Time: {max_response_time:.2f}s")
        print(f"Throughput: {throughput:.2f} requests/second")
        
        # Derby Day readiness assessment
        if success_rate >= 95 and avg_response_time < 3:
            print(f"\n🏆 DERBY DAY READY: ✅ EXCELLENT")
        elif success_rate >= 90 and avg_response_time < 5:
            print(f"\n🏆 DERBY DAY READY: ✅ GOOD")
        else:
            print(f"\n⚠️ DERBY DAY NEEDS OPTIMIZATION")
        
        print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    load_test = DerbyDayLoadTest()
    
    # Test with increasing load
    for users in [5, 10, 15]:
        print(f"\n{'='*60}")
        load_test.run_load_test(users)
        time.sleep(2)  # Brief pause between tests
