import subprocess
import sys

def setup_selenium_environment():
    """Setup Selenium for HKJC automation"""
    
    print("🔧 SETTING UP SELENIUM ENVIRONMENT")
    print("=" * 40)
    
    # Install required packages
    packages = [
        "selenium",
        "webdriver-manager", 
        "beautifulsoup4",
        "requests",
        "lxml"
    ]
    
    print("📦 Installing required packages:")
    for package in packages:
        print(f"   • Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} installed successfully")
        except:
            print(f"   ❌ Failed to install {package}")
    
    print("\n🎯 SELENIUM SETUP COMPLETE")
    print("Next: Create automation script")

def create_hkjc_automation_script():
    """Create HKJC automation script"""
    
    automation_script = '''
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import json

class HKJCAutomation:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
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
        options.add_argument('--disable-javascript')  # Can be enabled if needed
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver setup successful")
        except Exception as e:
            print(f"❌ Chrome driver setup failed: {e}")
            print("💡 Install ChromeDriver: brew install chromedriver")
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add human-like random delays"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def scroll_page(self):
        """Scroll page like human"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.human_like_delay(0.5, 1.5)
        self.driver.execute_script("window.scrollTo(0, 0);")
    
    def navigate_to_hkjc(self):
        """Navigate to HKJC racing page"""
        try:
            print("🌐 Navigating to HKJC...")
            self.driver.get("https://racing.hkjc.com")
            self.human_like_delay(3, 5)
            
            # Handle cookies if present
            try:
                cookie_button = self.driver.find_element(By.ID, "cookie-btn")
                cookie_button.click()
                self.human_like_delay(1, 2)
            except:
                pass
            
            # Navigate to racing section
            try:
                racing_link = self.driver.find_element(By.LINK_TEXT, "Racing")
                racing_link.click()
                self.human_like_delay(2, 3)
            except:
                # Try alternative navigation
                self.driver.get("https://racing.hkjc.com/racing/Info/Meeting/English/Local/")
                self.human_like_delay(3, 5)
            
            return True
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def extract_race_data(self):
        """Extract race data from current page"""
        try:
            print("📊 Extracting race data...")
            
            # Wait for page to load
            self.human_like_delay(2, 4)
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Look for race information
            race_data = {}
            
            # Extract venue
            venue_elements = soup.find_all(text=re.compile(r'Sha Tin|Happy Valley'))
            if venue_elements:
                race_data['venue'] = venue_elements[0].strip()
            
            # Extract races
            race_links = soup.find_all('a', href=re.compile(r'HR_Date='))
            races = []
            
            for link in race_links:
                race_text = link.get_text(strip=True)
                if re.search(r'Race\s+\d+', race_text):
                    races.append({
                        'link': link.get('href'),
                        'text': race_text
                    })
            
            race_data['races'] = races[:5]  # Limit to first 5 races
            
            print(f"✅ Found {len(races)} races")
            return race_data
            
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")
            return {}
    
    def get_race_details(self, race_url):
        """Get detailed information for a specific race"""
        try:
            print(f"🏇 Getting race details...")
            self.driver.get(race_url)
            self.human_like_delay(3, 5)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Extract horse information
            horse_data = []
            
            # Look for horse tables
            horse_rows = soup.find_all('tr', class_=re.compile(r'row|horse'))
            
            for row in horse_rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    try:
                        horse_info = {
                            'number': cells[0].get_text(strip=True),
                            'name': cells[1].get_text(strip=True),
                            'barrier': cells[2].get_text(strip=True),
                            'jockey': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                            'trainer': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                            'weight': cells[5].get_text(strip=True) if len(cells) > 5 else ''
                        }
                        horse_data.append(horse_info)
                    except:
                        continue
            
            return horse_data
            
        except Exception as e:
            print(f"❌ Race details failed: {e}")
            return []
    
    def run_automation(self):
        """Main automation workflow"""
        try:
            print("🚀 Starting HKJC automation...")
            
            if not self.navigate_to_hkjc():
                return False
            
            # Extract basic race data
            race_data = self.extract_race_data()
            
            if race_data.get('races'):
                # Get details for first race
                first_race = race_data['races'][0]
                if 'link' in first_race:
                    full_url = f"https://racing.hkjc.com{first_race['link']}"
                    horse_data = self.get_race_details(full_url)
                    
                    print(f"✅ Automation successful!")
                    print(f"📊 Found {len(horse_data)} horses")
                    
                    return {
                        'race_data': race_data,
                        'horse_data': horse_data
                    }
            
            return False
            
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

# Usage example
if __name__ == "__main__":
    automation = HKJCAutomation()
    result = automation.run_automation()
    
    if result:
        print("\\n🎯 AUTOMATION RESULTS:")
        print(json.dumps(result, indent=2))
    else:
        print("\\n❌ Automation failed")
'''
    
    with open('hkjc_automation_script.py', 'w') as f:
        f.write(automation_script)
    
    print("✅ HKJC automation script created: hkjc_automation_script.py")

def show_automation_caveats():
    """Show important warnings about automation"""
    
    print("\n⚠️  IMPORTANT WARNINGS:")
    print("=" * 30)
    print("• This may violate HKJC terms of service")
    print("• Could result in IP bans")
    print("• HKJC actively monitors for automation")
    print("• Use at your own risk")
    print("• Consider ethical implications")
    print("• Commercial use requires proper licensing")
    
    print("\n🛡️  PROTECTION MEASURES:")
    print("=" * 25)
    print("• Use rotating proxies")
    print("• Add random delays")
    print("• Limit request frequency")
    print("• Monitor for detection")
    print("• Have backup IP addresses")

if __name__ == "__main__":
    setup_selenium_environment()
    create_hkjc_automation_script()
    show_automation_caveats()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Install ChromeDriver: brew install chromedriver")
    print("2. Run: python3 hkjc_automation_script.py")
    print("3. Monitor for success/failure")
    print("4. Adjust as needed")
