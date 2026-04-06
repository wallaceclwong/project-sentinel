
import pyautogui
import time
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

class HKJCScreenScraper:
    def __init__(self):
        pyautogui.PAUSE = 1
        self.setup_regions()
    
    def setup_regions(self):
        """Define screen regions for HKJC app"""
        # These would need to be calibrated for your screen
        self.hkjc_app_region = (100, 100, 800, 600)  # x, y, width, height
        self.race_list_region = (150, 200, 700, 400)
        self.horse_info_region = (200, 300, 600, 200)
    
    def capture_hkjc_screen(self):
        """Capture HKJC app screen"""
        try:
            print("📸 Capturing HKJC screen...")
            
            # Take screenshot of specific region
            screenshot = pyautogui.screenshot(region=self.hkjc_app_region)
            
            # Save screenshot
            timestamp = int(time.time())
            filename = f"hkjc_screenshot_{timestamp}.png"
            screenshot.save(filename)
            
            print(f"✅ Screenshot saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """Extract text using OCR"""
        try:
            print("📝 Extracting text from image...")
            
            # Open image
            image = Image.open(image_path)
            
            # Preprocess for better OCR
            image = image.convert('L')  # Convert to grayscale
            image = image.resize((image.width * 2, image.height * 2))  # Upscale
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            print(f"✅ Text extracted: {len(text)} characters")
            return text
            
        except Exception as e:
            print(f"❌ OCR failed: {e}")
            return ""
    
    def parse_race_data(self, text):
        """Parse race data from extracted text"""
        try:
            print("🔍 Parsing race data...")
            
            race_data = {}
            
            # Look for venue
            if "Sha Tin" in text:
                race_data['venue'] = "Sha Tin"
            elif "Happy Valley" in text:
                race_data['venue'] = "Happy Valley"
            
            # Look for race numbers
            race_numbers = re.findall(r'Race\s+(\d+)', text, re.IGNORECASE)
            if race_numbers:
                race_data['races'] = list(set(race_numbers))[:6]
            
            # Look for horse patterns
            horse_patterns = re.findall(r'#(\d+)\s+([A-Za-z][A-Za-z0-9\s]+?)\s+(?:\d+|Barrier)', text)
            if horse_patterns:
                horses = []
                for pattern in horse_patterns[:10]:
                    horse_number = pattern[0]
                    horse_name = pattern[1].strip()
                    if len(horse_name) > 2:
                        horses.append({
                            'number': horse_number,
                            'name': horse_name
                        })
                race_data['horses'] = horses
            
            return race_data
            
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            return {}
    
    def automate_screen_scraping(self):
        """Main automation workflow"""
        try:
            print("🤖 Starting screen scraping automation...")
            print("⚠️  Make sure HKJC app is visible on screen")
            print()
            
            # Wait for user to position HKJC app
            input("Press Enter when HKJC app is ready...")
            
            # Capture screen
            image_path = self.capture_hkjc_screen()
            if not image_path:
                return False
            
            # Extract text
            text = self.extract_text_from_image(image_path)
            if not text:
                return False
            
            # Parse data
            race_data = self.parse_race_data(text)
            
            if race_data:
                print("\n🎯 SCREEN SCRAPING RESULTS:")
                print(f"Venue: {race_data.get('venue', 'Unknown')}")
                print(f"Races: {race_data.get('races', [])}")
                print(f"Horses: {len(race_data.get('horses', []))}")
                
                return race_data
            else:
                print("❌ No race data parsed")
                return False
                
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False

# Usage instructions
print("📸 HKJC SCREEN SCRAPING SETUP")
print("=" * 35)
print("Requirements:")
print("• HKJC app open on screen")
print("• Tesseract OCR installed")
print("• Python packages installed")
print()
print("Steps:")
print("1. Open HKJC app/website")
print("2. Position it visible on screen")
print("3. Run the automation")
print("4. OCR will extract race data")
print()
print("⚠️  This is semi-automated - requires manual setup")
