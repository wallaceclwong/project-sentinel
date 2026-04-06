import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json

class HKJCAutomationFixed:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with automatic version matching"""
        try:
            print("🔧 Setting up Chrome driver with automatic management...")
            
            options = Options()
            
            # Stealth options
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/145.0.0.0 Mobile/15E148 Safari/604.1'
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Use webdriver-manager to get correct version
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            print("✅ Chrome driver setup successful")
            return True
            
        except Exception as e:
            print(f"❌ Chrome driver setup failed: {e}")
            return False
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add human-like random delays"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def scroll_page(self):
        """Scroll page like human"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_like_delay(0.5, 1.5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.human_like_delay(0.5, 1.5)
        except:
            pass
    
    def navigate_to_hkjc(self):
        """Navigate to HKJC racing page"""
        try:
            print("🌐 Navigating to HKJC...")
            
            # Try different HKJC URLs
            urls = [
                "https://racing.hkjc.com",
                "https://racing.hkjc.com/racing/Info/Meeting/English/Local/",
                "https://www.hkjc.com/english/racing/"
            ]
            
            for url in urls:
                try:
                    print(f"   Trying: {url}")
                    self.driver.get(url)
                    self.human_like_delay(3, 5)
                    
                    # Check if page loaded
                    if "HKJC" in self.driver.title or "Hong Kong Jockey Club" in self.driver.page_source:
                        print(f"   ✅ Successfully loaded: {url}")
                        break
                        
                except Exception as e:
                    print(f"   ❌ Failed to load {url}: {e}")
                    continue
            
            # Handle cookies if present
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'I agree')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self.human_like_delay(1, 2)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def extract_race_data(self):
        """Extract race data from current page"""
        try:
            print("📊 Extracting race data...")
            
            self.human_like_delay(2, 4)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            race_data = {}
            
            # Look for race information
            if "Sha Tin" in page_source:
                race_data['venue'] = "Sha Tin"
            elif "Happy Valley" in page_source:
                race_data['venue'] = "Happy Valley"
            
            # Look for race numbers
            import re
            race_numbers = re.findall(r'Race\s+(\d+)', page_source, re.IGNORECASE)
            if race_numbers:
                race_data['races'] = list(set(race_numbers))[:6]  # First 6 unique races
                print(f"   ✅ Found {len(race_data['races'])} races: {race_data['races']}")
            
            # Look for horse information
            horse_patterns = re.findall(r'#(\d+)\s+([A-Za-z][A-Za-z0-9\s]+?)\s+(?:\d+|Barrier)', page_source)
            if horse_patterns:
                horses = []
                for pattern in horse_patterns[:10]:  # Limit to first 10
                    horse_number = pattern[0]
                    horse_name = pattern[1].strip()
                    horses.append({
                        'number': horse_number,
                        'name': horse_name
                    })
                race_data['horses'] = horses
                print(f"   ✅ Found {len(horses)} horses")
            
            return race_data
            
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")
            return {}
    
    def run_automation(self):
        """Main automation workflow"""
        try:
            print("🚀 Starting HKJC automation...")
            print("⚠️  This is for educational purposes only")
            print("⚠️  May violate HKJC terms of service")
            print()
            
            if not self.setup_driver():
                return False
            
            if not self.navigate_to_hkjc():
                return False
            
            # Extract data
            race_data = self.extract_race_data()
            
            if race_data:
                print("\n🎯 AUTOMATION RESULTS:")
                print(json.dumps(race_data, indent=2))
                return race_data
            else:
                print("\n❌ No data extracted")
                return False
                
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Browser closed")

# Test the automation
if __name__ == "__main__":
    automation = HKJCAutomationFixed()
    result = automation.run_automation()
    
    if result:
        print("\n✅ Automation completed successfully!")
        print("📊 Data extracted and ready for analysis")
    else:
        print("\n❌ Automation failed")
        print("💡 Try manual data entry instead")
