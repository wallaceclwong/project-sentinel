#!/usr/bin/env python3
"""
Check available Gemini models for your API key
"""

import os
import google.generativeai as genai

def load_api_key():
    """Load API key from environment or example file"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        try:
            with open('.env.example', 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            return None
    
    return api_key

def main():
    api_key = load_api_key()
    if not api_key:
        print("❌ API key not found!")
        return
    
    masked_key = api_key[:10] + "..." + api_key[-4:]
    print(f"🔑 API Key: {masked_key}")
    
    genai.configure(api_key=api_key)
    
    print("\n📋 Available Models:")
    print("=" * 50)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name} - {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Methods: {model.supported_generation_methods}")
            print()

if __name__ == "__main__":
    main()
