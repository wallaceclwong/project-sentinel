from playwright.sync_api import sync_playwright
import time
import random
import json

class HKJCPlaywrightAutomation:
    def __init__(self):
        self.browser = None
        self.page = None
    
    def setup_browser(self):
        """Setup Playwright browser"""
        try:
            print("🎭 Setting up Playwright browser...")
            self.playwright = sync_playwright().start()
            
            # Launch browser with stealth options
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-extensions'
                ]
            )
            
            # Create context with realistic user agent
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            self.page = context.new_page()
            
            # Add stealth scripts
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            print("✅ Playwright browser setup successful")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add human-like delays"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    async def navigate_to_hkjc(self):
        """Navigate to HKJC"""
        try:
            print("🌐 Navigating to HKJC with Playwright...")
            
            # Navigate to HKJC
            await self.page.goto("https://racing.hkjc.com/racing/Info/Meeting/English/Local/")
            await self.page.wait_for_load_state('networkidle')
            self.human_like_delay(2, 4)
            
            # Handle cookies
            try:
                accept_button = await self.page.query_selector("text=Accept")
                if accept_button:
                    await accept_button.click()
                    await self.page.wait_for_timeout(1000)
            except:
                pass
            
            # Check if page loaded
            title = await self.page.title()
            print(f"   ✅ Page loaded: {title}")
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    async def extract_race_data(self):
        """Extract race data"""
        try:
            print("📊 Extracting race data...")
            
            # Wait for content to load
            await self.page.wait_for_timeout(3000)
            
            # Try different selectors for race data
            selectors = [
                ".race-card",
                ".race-info",
                "[data-race]",
                ".meeting-info",
                "table",
                ".race-list"
            ]
            
            race_data = {}
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"   ✅ Found {len(elements)} elements with selector: {selector}")
                        
                        # Extract text from elements
                        texts = []
                        for element in elements[:5]:  # Limit to first 5
                            text = await element.text_content()
                            if text and len(text.strip()) > 0:
                                texts.append(text.strip())
                        
                        if texts:
                            race_data['extracted_data'] = texts
                            break
                            
                except:
                    continue
            
            # Get page content as fallback
            page_content = await self.page.content()
            
            # Look for race information in page content
            import re
            if "Sha Tin" in page_content:
                race_data['venue'] = "Sha Tin"
            elif "Happy Valley" in page_content:
                race_data['venue'] = "Happy Valley"
            
            # Look for race numbers
            race_numbers = re.findall(r'Race\s+(\d+)', page_content, re.IGNORECASE)
            if race_numbers:
                race_data['races'] = list(set(race_numbers))[:6]
                print(f"   ✅ Found {len(race_data['races'])} races: {race_data['races']}")
            
            # Look for horse patterns
            horse_patterns = re.findall(r'#(\d+)\s+([A-Za-z][A-Za-z0-9\s]+?)\s+(?:\d+|Barrier|Jockey)', page_content)
            if horse_patterns:
                horses = []
                for pattern in horse_patterns[:8]:
                    horse_number = pattern[0]
                    horse_name = pattern[1].strip()
                    if len(horse_name) > 2:  # Filter out short matches
                        horses.append({
                            'number': horse_number,
                            'name': horse_name
                        })
                race_data['horses'] = horses
                print(f"   ✅ Found {len(horses)} potential horses")
            
            return race_data
            
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")
            return {}
    
    async def run_automation(self):
        """Main automation workflow"""
        try:
            print("🎭 Starting HKJC Playwright automation...")
            print("⚠️  Educational purposes only")
            print("⚠️  May violate HKJC terms")
            print()
            
            if not self.setup_browser():
                return False
            
            if not await self.navigate_to_hkjc():
                return False
            
            race_data = await self.extract_race_data()
            
            if race_data:
                print("\n🎯 PLAYWRIGHT AUTOMATION RESULTS:")
                print(json.dumps(race_data, indent=2))
                return race_data
            else:
                print("\n❌ No data extracted")
                return False
                
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False
        finally:
            if self.browser:
                await self.browser.close()
                print("🔚 Browser closed")

# Note: This would be run with async/await
print("🎭 PLAYWRIGHT AUTOMATION READY")
print("💡 This requires async/await syntax to run")
print("🔧 More advanced than Selenium but often more reliable")
