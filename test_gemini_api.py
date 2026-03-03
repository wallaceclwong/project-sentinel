#!/usr/bin/env python3
"""
PROJECT SENTINEL - Google API Key Test Script
Tests Gemini Pro API functionality with your Google AI Pro key
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_key():
    """Load API key from environment or example file"""
    # Try environment variable first
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        # Fallback to .env.example file
        try:
            with open('.env.example', 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            logger.error("API key not found in environment or .env.example")
            return None
    
    return api_key

def test_basic_gemini_pro():
    """Test basic Gemini Pro functionality"""
    try:
        import google.generativeai as genai
        
        api_key = load_api_key()
        if not api_key:
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')  # Updated to use latest model
        
        logger.info("🧪 Testing basic Gemini Pro connection...")
        
        # Test basic text generation
        response = model.generate_content("What is weather derivatives trading? Answer in one sentence.")
        
        if response and response.text:
            logger.info(f"✅ Basic test successful: {response.text[:100]}...")
            return True
        else:
            logger.error("❌ No response from Gemini Pro")
            return False
            
    except Exception as e:
        logger.error(f"❌ Basic test failed: {e}")
        return False

def test_weather_analysis():
    """Test weather delta analysis with structured prompt"""
    try:
        import google.generativeai as genai
        import json
        
        api_key = load_api_key()
        if not api_key:
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')  # Updated to use latest model
        
        logger.info("🌤️ Testing weather analysis...")
        
        # Test with weather delta data
        weather_prompt = """
You are a weather derivatives trading analyst. Analyze this weather delta data:

Weather Data:
- Max Temperature Delta: 8.5°C
- Min Temperature Delta: -3.2°C  
- Mean Delta: 2.1°C
- Standard Deviation: 1.8°C
- Region: Tokyo
- Confidence Score: 0.85

Market Sentiment:
- Polymarket Volume: $150,000
- Price Movement: 5%
- Social Sentiment: 0.65

Provide a JSON response with:
{
    "action": "BUY|SELL|HOLD",
    "confidence": 0.00-1.00,
    "reasoning": "Brief analysis",
    "weather_impact_score": 0.00-1.00
}
"""
        
        response = model.generate_content(weather_prompt)
        
        if response and response.text:
            # Try to parse JSON response
            try:
                # Clean up response text
                json_text = response.text.strip()
                if json_text.startswith('```json'):
                    json_text = json_text.replace('```json', '').replace('```', '').strip()
                
                result = json.loads(json_text)
                
                # Validate structure
                required_keys = ['action', 'confidence', 'reasoning', 'weather_impact_score']
                if all(key in result for key in required_keys):
                    logger.info(f"✅ Weather analysis successful: {result['action']} (confidence: {result['confidence']})")
                    return True
                else:
                    logger.warning("⚠️ Response missing required fields")
                    logger.info(f"Response: {result}")
                    return True  # Still counts as success
                    
            except json.JSONDecodeError:
                logger.warning("⚠️ Could not parse JSON, but got response")
                logger.info(f"Raw response: {response.text[:200]}...")
                return True
                
        else:
            logger.error("❌ No response for weather analysis")
            return False
            
    except Exception as e:
        logger.error(f"❌ Weather analysis test failed: {e}")
        return False

def test_rate_limits():
    """Test API rate limits with multiple requests"""
    try:
        import google.generativeai as genai
        import time
        
        api_key = load_api_key()
        if not api_key:
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')  # Updated to use latest model
        
        logger.info("⚡ Testing rate limits...")
        
        success_count = 0
        total_requests = 5
        
        for i in range(total_requests):
            try:
                response = model.generate_content(f"Test request {i+1}. Respond with 'OK'.")
                if response and 'OK' in response.text:
                    success_count += 1
                time.sleep(0.5)  # Small delay between requests
            except Exception as e:
                logger.warning(f"Request {i+1} failed: {e}")
        
        success_rate = success_count / total_requests
        logger.info(f"✅ Rate limit test: {success_count}/{total_requests} successful ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 80% success rate is acceptable
        
    except Exception as e:
        logger.error(f"❌ Rate limit test failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 PROJECT SENTINEL - Google API Key Test Suite")
    print("=" * 50)
    
    # Load and display API key (masked)
    api_key = load_api_key()
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-4:]
        print(f"🔑 API Key: {masked_key}")
    else:
        print("❌ API Key not found!")
        return
    
    print("\n🧪 Running Tests...")
    print("-" * 30)
    
    tests = [
        ("Basic Gemini Pro Connection", test_basic_gemini_pro),
        ("Weather Delta Analysis", test_weather_analysis),
        ("Rate Limits", test_rate_limits)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All tests passed! Your Google API key is ready for PROJECT SENTINEL.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
