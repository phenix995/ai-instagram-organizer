#!/usr/bin/env python3
"""
Debug script to check Llama API response format
"""

import os
import json
import base64
import requests
from pathlib import Path

def image_to_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode('utf-8')

def debug_llama_response():
    """Debug the actual Llama API response format"""
    
    # Check for API key
    api_key = os.environ.get('LLAMA_API_KEY')
    if not api_key:
        print("❌ LLAMA_API_KEY environment variable not set")
        return False
    
    # Look for a test image
    test_image = None
    for ext in ['.jpg', '.jpeg', '.png']:
        for path in Path('.').glob(f'*{ext}'):
            test_image = str(path)
            break
        if test_image:
            break
    
    if not test_image:
        print("❌ No test image found")
        return False
    
    print(f"🖼️  Using test image: {test_image}")
    
    try:
        # Convert image to base64
        base64_image = image_to_base64(test_image)
        
        # Prepare API request
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
                            "text": "Describe this image briefly."
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
        
        print("🚀 Sending request to Llama API...")
        
        # Make API request
        response = requests.post(
            "https://api.llama.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        print("📋 Response Structure:")
        print(f"   Keys: {list(result.keys())}")
        
        # Pretty print the full response
        print("\n📄 Full Response:")
        print(json.dumps(result, indent=2))
        
        # Check for different possible content locations
        print("\n🔍 Content Analysis:")
        
        if 'choices' in result:
            print(f"   ✅ Has 'choices' key with {len(result['choices'])} items")
            if len(result['choices']) > 0:
                choice = result['choices'][0]
                print(f"   Choice keys: {list(choice.keys())}")
                if 'message' in choice:
                    print(f"   Message keys: {list(choice['message'].keys())}")
                    if 'content' in choice['message']:
                        content = choice['message']['content']
                        print(f"   Content preview: {content[:100]}...")
        else:
            print("   ❌ No 'choices' key found")
        
        if 'response' in result:
            print(f"   ✅ Has 'response' key: {result['response'][:100]}...")
        
        if 'content' in result:
            print(f"   ✅ Has 'content' key: {result['content'][:100]}...")
        
        if 'message' in result:
            print(f"   ✅ Has 'message' key: {result['message'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Llama API Response Format")
    print("=" * 50)
    
    debug_llama_response()