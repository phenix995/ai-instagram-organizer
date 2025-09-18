#!/usr/bin/env python3
"""
Test multi-provider functionality
"""

import os
import json
import base64
import requests
from pathlib import Path

def test_llama_api():
    """Test Llama API"""
    api_key = "***REMOVED_LLAMA_API_KEY***"
    
    test_image = "test_image_complex.jpg"
    if not os.path.exists(test_image):
        print("❌ Test image not found")
        return False
    
    with open(test_image, "rb") as img:
        base64_image = base64.b64encode(img.read()).decode('utf-8')
    
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
                        "text": "Analyze this image briefly."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.llama.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"🦙 Llama API Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Llama API working")
            return True
        else:
            print(f"❌ Llama API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Llama API failed: {e}")
        return False

def test_gemini_api():
    """Test Gemini API"""
    api_key = "***REMOVED_GEMINI_API_KEY***"
    
    test_image = "test_image_complex.jpg"
    if not os.path.exists(test_image):
        print("❌ Test image not found")
        return False
    
    with open(test_image, "rb") as img:
        base64_image = base64.b64encode(img.read()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this image briefly."},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"🤖 Gemini API Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Gemini API working")
            return True
        else:
            print(f"❌ Gemini API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Multi-Provider APIs")
    print("=" * 40)
    
    llama_ok = test_llama_api()
    print()
    gemini_ok = test_gemini_api()
    
    print("\n📊 Results:")
    print(f"Llama API: {'✅ Working' if llama_ok else '❌ Failed'}")
    print(f"Gemini API: {'✅ Working' if gemini_ok else '❌ Failed'}")
    
    if llama_ok and gemini_ok:
        print("\n🚀 Both APIs working - Multi-provider ready!")
    elif llama_ok:
        print("\n⚡ Llama only - Still much faster than before!")
    else:
        print("\n❌ API issues detected")