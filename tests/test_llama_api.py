#!/usr/bin/env python3
"""
Test script for Llama API integration
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

def test_llama_api():
    """Test Llama API with a sample image"""
    
    # Check for API key
    api_key = os.environ.get('LLAMA_API_KEY')
    if not api_key:
        print("❌ LLAMA_API_KEY environment variable not set")
        print("Please set it with: export LLAMA_API_KEY='your-api-key'")
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
        print("❌ No test image found. Please add a .jpg, .jpeg, or .png file to the current directory")
        return False
    
    print(f"🖼️  Using test image: {test_image}")
    
    try:
        # Convert image to base64
        base64_image = image_to_base64(test_image)
        print("✅ Image converted to base64")
        
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
                            "text": "What does this image contain? Describe it briefly."
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
        
        response.raise_for_status()
        result = response.json()
        
        # Handle Llama API response format
        if 'completion_message' in result and 'content' in result['completion_message']:
            content_obj = result['completion_message']['content']
            if isinstance(content_obj, dict) and 'text' in content_obj:
                content = content_obj['text']
            elif isinstance(content_obj, str):
                content = content_obj
            else:
                content = str(content_obj)
            
            print("✅ Llama API response received:")
            print(f"📝 {content}")
            return True
        else:
            print("❌ No valid response from Llama API")
            print(f"Response: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🦙 Testing Llama API Integration")
    print("=" * 40)
    
    success = test_llama_api()
    
    if success:
        print("\n✅ Llama API integration test passed!")
        print("You can now use the Instagram organizer with Llama API.")
    else:
        print("\n❌ Llama API integration test failed!")
        print("Please check your API key and network connection.")