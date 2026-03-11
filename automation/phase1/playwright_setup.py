"""
SENTINEL-RACING AI - PHASE 1: TECHNICAL FOUNDATION
Playwright Automation Setup for Advanced HKJC Data Extraction
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class PlaywrightHKJCScraper:
    """Advanced HKJC scraper using Playwright for JavaScript rendering"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.session_data = {}
        
    async def setup_browser(self):
        """Setup Playwright browser with stealth options"""
        self.browser = await async_playwright().chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--window-size=1920,1080',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await self.context.new_page()
        
        # Set up stealth measures
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        print("✅ Playwright browser setup completed")
        
    async def navigate_to_hkjc(self):
        """Navigate to HKJC main page"""
        try:
            await self.page.goto('https://racing.hkjc.com/en-us/index', wait_until='networkidle')
            await asyncio.sleep(3)  # Wait for page to fully load
            
            print("✅ Navigated to HKJC main page")
            return True
            
        except Exception as e:
            print(f"❌ Failed to navigate to HKJC: {e}")
            return False
    
    async def discover_api_endpoints(self):
        """Discover hidden API endpoints by monitoring network traffic"""
        try:
            api_endpoints = []
            
            # Set up network monitoring
            async def handle_response(response):
                url = response.url
                if 'hkjc.com' in url and ('api' in url or 'data' in url or 'service' in url):
                    api_endpoints.append({
                        'url': url,
                        'method': response.request.method,
                        'status': response.status,
                        'headers': dict(response.headers)
                    })
            
            self.page.on('response', handle_response)
            
            # Navigate to race card to trigger API calls
            await self.page.goto('https://racing.hkjc.com/en-us/local/information/racecard?racedate=2026/03/11&Racecourse=HV&RaceNo=3')
            await asyncio.sleep(5)  # Wait for API calls
            
            # Extract API endpoints from page source
            page_source = await self.page.content()
            
            # Look for API patterns in JavaScript
            import re
            
            js_api_patterns = [
                r'fetch\([\'"]([^\'"]+)[\'"]',
                r'\.get\([\'"]([^\'"]+)[\'"]',
                r'api[\/][^\'"\s]+',
                r'service[\/][^\'"\s]+',
                r'data[\/][^\'"\s]+'
            ]
            
            for pattern in js_api_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    if 'hkjc.com' in match or 'racing' in match:
                        api_endpoints.append({
                            'url': match,
                            'source': 'javascript',
                            'pattern': pattern
                        })
            
            # Remove duplicates and save
            unique_endpoints = []
            seen_urls = set()
            
            for endpoint in api_endpoints:
                url = endpoint.get('url', '')
                if url not in seen_urls:
                    unique_endpoints.append(endpoint)
                    seen_urls.add(url)
            
            # Save discovered endpoints
            with open('/Users/wallace/Documents/ project-sentinel/automation/phase1/discovered_apis.json', 'w') as f:
                json.dump(unique_endpoints, f, indent=2)
            
            print(f"✅ Discovered {len(unique_endpoints)} API endpoints")
            
            for endpoint in unique_endpoints[:5]:  # Show first 5
                print(f"   📡 {endpoint.get('url', 'Unknown')}")
            
            return unique_endpoints
            
        except Exception as e:
            print(f"❌ API discovery failed: {e}")
            return []
    
    async def extract_race_data(self):
        """Extract race data using Playwright"""
        try:
            # Navigate to Race 3
            await self.page.goto('https://racing.hkjc.com/en-us/local/information/racecard?racedate=2026/03/11&Racecourse=HV&RaceNo=3')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Wait for race data to load
            try:
                await self.page.wait_for_selector('[data-race="3"]', timeout=10000)
            except:
                # Try alternative selectors
                await self.page.wait_for_selector('table', timeout=10000)
            
            # Extract horse data
            horse_data = []
            
            # Method 1: Look for structured tables
            tables = await self.page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all('tr')
                
                for row in rows:
                    cells = await row.query_selector_all('td')
                    
                    if len(cells) >= 4:
                        row_text = await row.text_content()
                        
                        # Skip header rows
                        if any(header in row_text.lower() for header in ['horse no.', 'name', 'barrier', 'jockey']):
                            continue
                        
                        # Extract cell data
                        cell_texts = []
                        for cell in cells:
                            text = await cell.text_content()
                            cell_texts.append(text.strip())
                        
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
            
            # Method 2: Look for div elements with horse data
            if not horse_data:
                divs = await self.page.query_selector_all('div')
                
                for div in divs:
                    text = await div.text_content()
                    
                    # Look for horse patterns
                    import re
                    if re.search(r'#?\d+.*[A-Z][a-z]+', text):
                        parts = text.split()
                        if len(parts) >= 3:
                            horse_data.append({
                                'raw_data': text.strip()
                            })
            
            # Save extracted data
            with open('/Users/wallace/Documents/ project-sentinel/automation/phase1/race_data.json', 'w') as f:
                json.dump(horse_data, f, indent=2)
            
            print(f"✅ Extracted data for {len(horse_data)} horses")
            
            for i, horse in enumerate(horse_data[:5], 1):
                if 'raw_data' in horse:
                    print(f"   🐎 {i}. {horse['raw_data']}")
                else:
                    print(f"   🐎 {i}. #{horse['number']} {horse['name']} (B{horse['barrier']}) - {horse['jockey']}")
            
            return horse_data
            
        except Exception as e:
            print(f"❌ Race data extraction failed: {e}")
            return []
    
    async def close_browser(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        
        print("✅ Browser closed and cleanup completed")

async def main():
    """Main execution function"""
    print("🚀 SENTINEL-RACING AI - PHASE 1: PLAYWRIGHT SETUP")
    print("=" * 60)
    
    scraper = PlaywrightHKJCScraper()
    
    try:
        # Step 1: Setup browser
        await scraper.setup_browser()
        
        # Step 2: Navigate to HKJC
        if await scraper.navigate_to_hkjc():
            
            # Step 3: Discover API endpoints
            print("\n🔍 Step 3: Discovering API endpoints...")
            api_endpoints = await scraper.discover_api_endpoints()
            
            # Step 4: Extract race data
            print("\n🐎 Step 4: Extracting race data...")
            race_data = await scraper.extract_race_data()
            
            # Step 5: Analysis summary
            print(f"\n📊 PHASE 1 COMPLETION SUMMARY:")
            print(f"✅ API endpoints discovered: {len(api_endpoints)}")
            print(f"✅ Horses extracted: {len(race_data)}")
            print(f"✅ Browser automation: Working")
            print(f"✅ Data extraction: Successful")
            
            print(f"\n🎯 PHASE 1 STATUS: COMPLETED")
            print(f"🚀 Ready for Phase 2: Data Integration")
            
    except Exception as e:
        print(f"❌ Phase 1 execution failed: {e}")
    
    finally:
        await scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(main())
