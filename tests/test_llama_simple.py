#!/usr/bin/env python3
"""
Simple test for Llama API without image
"""

import os
import json
import requests

def test_llama_simple():
    """Test Llama API with text-only request"""
    
    # Check for API key
    api_key = os.environ.get('LLAMA_API_KEY')
    
    if not api_key:
        print("❌ Error: API key is not set.")
        return False
    
    print(f"🔑 Using API key: {api_key[:20]}...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello, can you respond with a simple JSON object like this: {\"test\": \"success\", \"message\": \"API is working\"}?"
                    }
                ]
            }
        ]
    }
    
    try:
        print("🚀 Testing Llama API...")
        
        response = requests.post(
            "https://api.llama.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        print("📋 Response Structure:")
        print(f"   Keys: {list(result.keys())}")
        
        print("\n📄 Full Response:")
        print(json.dumps(result, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_llama_simple()