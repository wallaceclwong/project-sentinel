"""
SENTINEL-RACING AI - PHASE 1: API DISCOVERY
Advanced HKJC API Endpoint Discovery and Testing
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

class HKJCAPIDiscovery:
    """Advanced API discovery for HKJC racing data"""
    
    def __init__(self):
        self.base_url = "https://racing.hkjc.com"
        self.discovered_apis = []
        self.session = None
        self.test_results = {}
        
    async def setup_session(self):
        """Setup HTTP session with proper headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-HK;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
        print("✅ HTTP session setup completed")
    
    async def discover_from_page_source(self, url: str) -> List[Dict]:
        """Discover API endpoints from page source"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Look for API patterns in JavaScript
                    api_patterns = [
                        r'fetch\([\'"]([^\'"]+)[\'"]',
                        r'\.get\([\'"]([^\'"]+)[\'"]',
                        r'\.post\([\'"]([^\'"]+)[\'"]',
                        r'api[\/][^\'"\s]+',
                        r'service[\/][^\'"\s]+',
                        r'data[\/][^\'"\s]+',
                        r'endpoint[\/][^\'"\s]+',
                        r'/api/[^\'"\s]+',
                        r'/service/[^\'"\s]+',
                        r'/data/[^\'"\s]+'
                    ]
                    
                    discovered = []
                    for pattern in api_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if 'hkjc.com' in match or 'racing' in match:
                                full_url = urljoin(self.base_url, match)
                                discovered.append({
                                    'url': full_url,
                                    'source': 'page_source',
                                    'pattern': pattern,
                                    'method': 'GET'
                                })
                    
                    # Remove duplicates
                    unique_apis = []
                    seen_urls = set()
                    
                    for api in discovered:
                        if api['url'] not in seen_urls:
                            unique_apis.append(api)
                            seen_urls.add(api['url'])
                    
                    return unique_apis
                
        except Exception as e:
            print(f"❌ Failed to discover from page source: {e}")
            return []
    
    async def discover_from_network(self, url: str) -> List[Dict]:
        """Discover API endpoints by monitoring network requests"""
        try:
            # This would typically be done with browser automation
            # For now, we'll simulate by trying common API patterns
            
            common_patterns = [
                '/api/racing/meetings',
                '/api/racing/races',
                '/api/racing/horses',
                '/api/racing/jockeys',
                '/api/racing/odds',
                '/api/racing/results',
                '/service/racing/data',
                '/data/racing/current',
                '/en-us/api/racing',
                '/racing/api/v1',
                '/mobile/api/racing'
            ]
            
            discovered = []
            for pattern in common_patterns:
                full_url = urljoin(self.base_url, pattern)
                discovered.append({
                    'url': full_url,
                    'source': 'network_pattern',
                    'pattern': pattern,
                    'method': 'GET'
                })
            
            return discovered
            
        except Exception as e:
            print(f"❌ Failed to discover from network: {e}")
            return []
    
    async def test_api_endpoint(self, api_info: Dict) -> Dict:
        """Test discovered API endpoint"""
        url = api_info['url']
        method = api_info.get('method', 'GET')
        
        try:
            if method == 'GET':
                async with self.session.get(url) as response:
                    content = await response.text()
                    
                    result = {
                        'url': url,
                        'method': method,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'content_length': len(content),
                        'content_type': response.headers.get('content-type', 'unknown'),
                        'success': response.status == 200,
                        'data_sample': content[:500] if len(content) > 0 else ''
                    }
                    
                    # Try to parse as JSON
                    if 'application/json' in result['content_type']:
                        try:
                            json_data = await response.json()
                            result['json_keys'] = list(json_data.keys())[:10] if isinstance(json_data, dict) else []
                            result['is_json'] = True
                        except:
                            result['is_json'] = False
                    else:
                        result['is_json'] = False
                    
                    return result
                    
            else:
                # Try POST requests if needed
                pass
                
        except Exception as e:
            return {
                'url': url,
                'method': method,
                'status': 'ERROR',
                'error': str(e),
                'success': False
            }
    
    async def discover_all_apis(self):
        """Discover all possible API endpoints"""
        print("🔍 Starting comprehensive API discovery...")
        
        # URLs to check
        urls_to_check = [
            'https://racing.hkjc.com/en-us/index',
            'https://racing.hkjc.com/en-us/local/information/racecard',
            'https://racing.hkjc.com/en-us/local/information/entries',
            'https://racing.hkjc.com/en-us/local/information/horse',
            'https://racing.hkjc.com/en-us/local/info/jockey-ranking'
        ]
        
        all_discovered = []
        
        for url in urls_to_check:
            print(f"🔍 Checking: {url}")
            
            # Discover from page source
            page_apis = await self.discover_from_page_source(url)
            all_discovered.extend(page_apis)
            
            # Discover from network patterns
            network_apis = await self.discover_from_network(url)
            all_discovered.extend(network_apis)
            
            await asyncio.sleep(1)  # Be respectful
        
        # Remove duplicates
        unique_apis = []
        seen_urls = set()
        
        for api in all_discovered:
            if api['url'] not in seen_urls:
                unique_apis.append(api)
                seen_urls.add(api['url'])
        
        print(f"✅ Discovered {len(unique_apis)} unique API endpoints")
        
        # Test all discovered endpoints
        print("🧪 Testing API endpoints...")
        
        for i, api in enumerate(unique_apis):
            print(f"🧪 Testing {i+1}/{len(unique_apis)}: {api['url']}")
            
            result = await self.test_api_endpoint(api)
            self.test_results[api['url']] = result
            
            if result['success']:
                print(f"   ✅ SUCCESS - Status: {result['status']}")
            else:
                print(f"   ❌ FAILED - {result.get('error', 'Unknown error')}")
            
            await asyncio.sleep(0.5)  # Be respectful
        
        # Save results
        discovery_data = {
            'discovered_apis': unique_apis,
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat(),
            'total_apis': len(unique_apis),
            'successful_tests': sum(1 for r in self.test_results.values() if r.get('success', False))
        }
        
        with open('/Users/wallace/Documents/ project-sentinel/automation/phase1/api_discovery_results.json', 'w') as f:
            json.dump(discovery_data, f, indent=2)
        
        return discovery_data
    
    async def get_working_apis(self) -> List[Dict]:
        """Get list of working API endpoints"""
        working_apis = []
        
        for api_info in self.discovered_apis:
            url = api_info['url']
            if url in self.test_results:
                result = self.test_results[url]
                if result.get('success', False):
                    working_apis.append({
                        **api_info,
                        'test_result': result
                    })
        
        return working_apis
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
        
        print("✅ HTTP session closed")

async def main():
    """Main execution function"""
    print("🚀 SENTINEL-RACING AI - PHASE 1: API DISCOVERY")
    print("=" * 60)
    
    discovery = HKJCAPIDiscovery()
    
    try:
        # Setup session
        await discovery.setup_session()
        
        # Discover all APIs
        discovery_data = await discovery.discover_all_apis()
        
        # Get working APIs
        working_apis = await discovery.get_working_apis()
        
        # Display results
        print(f"\n📊 API DISCOVERY SUMMARY:")
        print(f"✅ Total APIs discovered: {discovery_data['total_apis']}")
        print(f"✅ Successful tests: {discovery_data['successful_tests']}")
        print(f"✅ Working APIs: {len(working_apis)}")
        
        print(f"\n🎯 WORKING API ENDPOINTS:")
        for i, api in enumerate(working_apis[:5], 1):
            print(f"   {i}. {api['url']}")
            print(f"      Status: {api['test_result']['status']}")
            print(f"      Content-Type: {api['test_result']['content_type']}")
        
        if len(working_apis) > 5:
            print(f"   ... and {len(working_apis) - 5} more")
        
        print(f"\n🎯 PHASE 1 API DISCOVERY: COMPLETED")
        print(f"🚀 Ready for enhanced data collection")
        
    except Exception as e:
        print(f"❌ API discovery failed: {e}")
    
    finally:
        await discovery.close_session()

if __name__ == "__main__":
    asyncio.run(main())
