import requests
import json
from datetime import datetime
import re

def try_hkjc_apis():
    """Try different HKJC API endpoints"""
    
    print("🏆 ATTEMPTING TO FETCH REAL HKJC DATA")
    print("=" * 45)
    
    # Try different HKJC endpoints
    endpoints = [
        "https://racing.hkjc.com/racing/Info/Meeting/English/Local/",
        "https://racing.hkjc.com/racing/Info/Meeting/English/Local/HR/",
        "https://racing.hkjc.com/racing/odds/English/Local/",
        "https://www.hkjc.com/english/racing/info/panel_sub_odds_winplace.aspx",
        "https://racing.hkjc.com/racing/information/English/Racing/Local.aspx",
        "https://racing.hkjc.com/racing/pages/odds_winplace.aspx"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for url in endpoints:
        try:
            print(f"🔍 Trying: {url}")
            response = requests.get(url, timeout=15, headers=headers)
            
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Content-Length: {len(response.text)}")
            
            if response.status_code == 200:
                content = response.text
                
                # Look for race information
                if "Sha Tin" in content or "Happy Valley" in content:
                    print(f"   ✅ Found race meeting info")
                    
                    # Try to extract race data
                    race_matches = re.findall(r'Race\s+(\d+)', content, re.IGNORECASE)
                    if race_matches:
                        print(f"   📊 Found races: {race_matches[:5]}")
                    
                    # Look for horse numbers
                    horse_matches = re.findall(r'#(\d+)', content)
                    if horse_matches:
                        print(f"   🐎 Found horse numbers: {horse_matches[:10]}")
                    
                    # Look for distances
                    distance_matches = re.findall(r'(\d{3,4})m', content)
                    if distance_matches:
                        print(f"   🏁 Found distances: {distance_matches[:5]}")
                    
                    print(f"   📄 Sample content: {content[:200]}...")
                    return content
                    
            else:
                print(f"   ❌ Failed to access")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    return None

def try_hkjc_mobile():
    """Try HKJC mobile version"""
    
    print("📱 TRYING HKJC MOBILE VERSION")
    print("=" * 35)
    
    mobile_urls = [
        "https://m.racing.hkjc.com",
        "https://mobile.hkjc.com",
        "https://racing.hkjc.com/racing/Info/Meeting/English/Local/?m=1"
    ]
    
    for url in mobile_urls:
        try:
            print(f"📱 Trying mobile: {url}")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            })
            
            if response.status_code == 200:
                print(f"   ✅ Mobile access successful")
                return response.text
                
        except Exception as e:
            print(f"   ❌ Mobile error: {e}")
    
    return None

def try_hkjc_json_apis():
    """Try to find HKJC JSON APIs"""
    
    print("🔍 TRYING HKJC JSON APIS")
    print("=" * 30)
    
    # Common HKJC API patterns
    api_patterns = [
        "https://racing.hkjc.com/racing/api/odds/winplace",
        "https://api.hkjc.com/racing/odds",
        "https://racing.hkjc.com/api/meeting",
        "https://www.hkjc.com/football/api/odds"  # Football API as reference
    ]
    
    for api_url in api_patterns:
        try:
            print(f"🔍 Trying API: {api_url}")
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON API found: {type(data)}")
                    print(f"   📊 Data: {str(data)[:200]}...")
                    return data
                except:
                    print(f"   ✅ API responds but not JSON")
                    
        except Exception as e:
            print(f"   ❌ API error: {e}")
    
    return None

def check_alternative_sources():
    """Check alternative racing data sources"""
    
    print("🌍 CHECKING ALTERNATIVE SOURCES")
    print("=" * 35)
    
    # Try racing data aggregators
    sources = [
        "https://www.racingpost.com",
        "https://www.timeform.com",
        "https://www.horseracing.net"
    ]
    
    for source in sources:
        try:
            print(f"🔍 Checking: {source}")
            response = requests.get(source, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Source accessible")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    print("🏆 HKJC REAL DATA FETCH ATTEMPT")
    print("=" * 40)
    print(f"⏰ Time: {datetime.now()}")
    print()
    
    # Try different approaches
    content = try_hkjc_apis()
    
    if not content:
        content = try_hkjc_mobile()
    
    if not content:
        data = try_hkjc_json_apis()
    
    if not content and not data:
        check_alternative_sources()
    
    print()
    print("🎯 SUMMARY:")
    if content or data:
        print("✅ Some data access achieved")
        print("📊 Need to parse and extract race information")
    else:
        print("❌ No real HKJC data access available")
        print("🔒 HKJC blocks automated data access")
        print("💡 Manual data entry required for real analysis")
    
    print()
    print("🏆 SENTINEL-RACING AI INTELLIGENCE")
    print(f"📊 Analysis completed: {datetime.now()}")
