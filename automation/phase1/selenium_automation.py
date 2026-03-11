"""
SENTINEL-RACING AI - PHASE 1: SELENIUM AUTOMATION
Selenium-based automation as fallback for Playwright issues
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import re
from datetime import datetime

class SeleniumHKJCScraper:
    """Selenium-based HKJC scraper"""
    
    def __init__(self):
        self.driver = None
        self.results = {}
        
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        try:
            # Setup Chrome options
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Install and setup driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            print("✅ Selenium Chrome driver setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Selenium setup failed: {e}")
            return False
    
    def navigate_to_hkjc(self):
        """Navigate to HKJC main page"""
        try:
            self.driver.get('https://racing.hkjc.com/en-us/index')
            time.sleep(3)  # Wait for page to load
            
            print("✅ Navigated to HKJC main page")
            return True
            
        except Exception as e:
            print(f"❌ Failed to navigate to HKJC: {e}")
            return False
    
    def extract_race_data(self):
        """Extract race data from HKJC"""
        try:
            # Navigate to Race 3
            self.driver.get('https://racing.hkjc.com/en-us/local/information/racecard?racedate=2026/03/11&Racecourse=HV&RaceNo=3')
            time.sleep(5)  # Wait for page to load
            
            # Get page title
            title = self.driver.title
            print(f"📄 Page title: {title}")
            
            # Check page content
            page_source = self.driver.page_source
            
            if 'Race 3' in page_source:
                print("✅ Race 3 found in page content")
            else:
                print("❌ Race 3 not found in page content")
            
            if 'Happy Valley' in page_source:
                print("✅ Happy Valley found in page content")
            else:
                print("❌ Happy Valley not found in page content")
            
            # Look for tables
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            print(f"📊 Found {len(tables)} tables")
            
            # Extract horse data
            horse_data = []
            
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    
                    if len(cells) >= 4:
                        row_text = row.text.strip()
                        
                        # Skip header rows
                        if any(header in row_text.lower() for header in ['horse no.', 'name', 'barrier', 'jockey']):
                            continue
                        
                        # Extract cell data
                        cell_texts = [cell.text.strip() for cell in cells]
                        
                        # Look for horse number pattern
                        for i, cell_text in enumerate(cell_texts):
                            if cell_text.isdigit() and i < 3:
                                horse_num = cell_text
                                horse_name = cell_texts[i+1] if i+1 < len(cell_texts) else 'Unknown'
                                barrier = cell_texts[i+2] if i+2 < len(cell_texts) else 'Unknown'
                                jockey = cell_texts[i+3] if i+3 < len(cell_texts) else 'Unknown'
                                
                                if horse_name != 'Unknown' and len(horse_name) > 2:
                                    horse_data.append({
                                        'number': horse_num,
                                        'name': horse_name,
                                        'barrier': barrier,
                                        'jockey': jockey
                                    })
                                break
            
            # Look for horse patterns in page source
            if not horse_data:
                horse_patterns = re.findall(r'#\d+\s+[A-Za-z][A-Za-z0-9\s&-]{3,25}', page_source)
                
                for pattern in horse_patterns:
                    parts = pattern.split()
                    if len(parts) >= 2:
                        horse_num = parts[0].replace('#', '')
                        horse_name = ' '.join(parts[1:])
                        horse_data.append({
                            'number': horse_num,
                            'name': horse_name,
                            'barrier': 'Unknown',
                            'jockey': 'Unknown'
                        })
            
            # Save results
            results = {
                'timestamp': datetime.now().isoformat(),
                'page_title': title,
                'tables_found': len(tables),
                'horses_extracted': len(horse_data),
                'horse_data': horse_data,
                'page_source_length': len(page_source),
                'success': True
            }
            
            with open('/Users/wallace/Documents/ project-sentinel/automation/phase1/selenium_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"✅ Extracted data for {len(horse_data)} horses")
            
            for i, horse in enumerate(horse_data[:5], 1):
                if horse['barrier'] != 'Unknown' and horse['jockey'] != 'Unknown':
                    print(f"   🐎 {i}. #{horse['number']} {horse['name']} (B{horse['barrier']}) - {horse['jockey']}")
                else:
                    print(f"   🐎 {i}. #{horse['number']} {horse['name']}")
            
            return results
            
        except Exception as e:
            print(f"❌ Race data extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_api_discovery(self):
        """Test API discovery with Selenium"""
        try:
            print("🔍 Testing API discovery...")
            
            # Monitor network requests (basic approach)
            page_source = self.driver.page_source
            
            # Look for API patterns in page source
            api_patterns = [
                r'fetch\([\'"]([^\'"]+)[\'"]',
                r'\.get\([\'"]([^\'"]+)[\'"]',
                r'api[\/][^\'"\s]+',
                r'service[\/][^\'"\s]+',
                r'data[\/][^\'"\s]+'
            ]
            
            discovered_apis = []
            
            for pattern in api_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    if 'hkjc.com' in match or 'racing' in match:
                        discovered_apis.append({
                            'url': match,
                            'pattern': pattern,
                            'source': 'page_source'
                        })
            
            # Remove duplicates
            unique_apis = []
            seen_urls = set()
            
            for api in discovered_apis:
                if api['url'] not in seen_urls:
                    unique_apis.append(api)
                    seen_urls.add(api['url'])
            
            print(f"✅ Discovered {len(unique_apis)} potential API endpoints")
            
            for i, api in enumerate(unique_apis[:5], 1):
                print(f"   📡 {i}. {api['url']}")
            
            return unique_apis
            
        except Exception as e:
            print(f"❌ API discovery failed: {e}")
            return []
    
    def close_driver(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
            print("✅ Selenium driver closed")
    
    def run_full_test(self):
        """Run complete Selenium test"""
        print("🚀 SENTINEL-RACING AI - PHASE 1: SELENIUM AUTOMATION")
        print("=" * 55)
        
        try:
            # Setup driver
            if self.setup_driver():
                
                # Navigate to HKJC
                if self.navigate_to_hkjc():
                    
                    # Extract race data
                    print("\n🐎 Extracting race data...")
                    results = self.extract_race_data()
                    
                    # Test API discovery
                    print("\n🔍 Testing API discovery...")
                    apis = self.test_api_discovery()
                    
                    # Summary
                    if results.get('success', False):
                        print(f"\n📊 SELENIUM TEST SUMMARY:")
                        print(f"✅ Selenium: Working")
                        print(f"✅ Browser automation: Successful")
                        print(f"✅ Page navigation: Completed")
                        print(f"✅ Data extraction: {results['horses_extracted']} horses")
                        print(f"✅ API discovery: {len(apis)} endpoints")
                        
                        print(f"\n🎯 PHASE 1 STATUS: SELENIUM WORKING")
                        print(f"🚀 Ready for Phase 2: Data Integration")
                        
                        return True
                    else:
                        print(f"\n❌ Data extraction failed")
                        return False
                else:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"❌ Selenium test failed: {e}")
            return False
        finally:
            self.close_driver()

if __name__ == "__main__":
    scraper = SeleniumHKJCScraper()
    success = scraper.run_full_test()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. ✅ Selenium automation working")
        print("2. 📋 Enhanced data collection")
        print("3. 🔍 API endpoint testing")
        print("4. 🚀 Proceed to Phase 2")
    else:
        print("\n❌ Selenium needs troubleshooting")
        print("🔧 Check Chrome driver installation")
