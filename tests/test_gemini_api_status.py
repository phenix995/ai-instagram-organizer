#!/usr/bin/env python3
"""
Simple test to check Gemini API status and limits
"""

import requests
import json
import time
import base64
from PIL import Image, ImageDraw

def create_simple_test_image():
    """Create a minimal test image"""
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Test", fill=(255, 255, 255))
    
    img.save("simple_test.jpg", quality=95)
    return "simple_test.jpg"

def test_gemini_api_simple():
    """Test Gemini API with minimal request"""
    print("🔧 Testing Gemini API Status")
    print("=" * 40)
    
    api_key = "***REMOVED_GEMINI_API_KEY***"
    
    # Create test image
    test_image = create_simple_test_image()
    
    with open(test_image, "rb") as img:
        base64_image = base64.b64encode(img.read()).decode('utf-8')
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "What do you see in this image? Answer in one sentence."},
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
            "maxOutputTokens": 100,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    print(f"API URL: {url}")
    print(f"Payload size: {len(json.dumps(payload))} bytes")
    print(f"Image size: {len(base64_image)} characters")
    
    try:
        print("\nMaking API request...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        duration = time.time() - start_time
        
        print(f"Response status: {response.status_code}")
        print(f"Response time: {duration:.2f}s")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Error response: {response.text}")
            
            # Check for specific error types
            if response.status_code == 429:
                print("🚨 Rate limit exceeded - API key may have hit daily/hourly limits")
            elif response.status_code == 403:
                print("🚨 Forbidden - API key may be invalid or restricted")
            elif response.status_code == 400:
                print("🚨 Bad request - Check payload format")
            
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    finally:
        # Clean up
        import os
        if os.path.exists(test_image):
            os.remove(test_image)

def test_multiple_requests():
    """Test multiple requests to see rate limiting behavior"""
    print("\n🔧 Testing Multiple Requests")
    print("=" * 40)
    
    api_key = "***REMOVED_GEMINI_API_KEY***"
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
    
    # Simple text-only request to minimize payload
    payload = {
        "contents": [{
            "parts": [{"text": "Say hello in one word."}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 10,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    success_count = 0
    rate_limit_count = 0
    
    for i in range(5):  # Test 5 requests
        print(f"\nRequest {i+1}:")
        
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            duration = time.time() - start_time
            
            print(f"  Status: {response.status_code}, Time: {duration:.2f}s")
            
            if response.status_code == 200:
                success_count += 1
                print("  ✅ Success")
            elif response.status_code == 429:
                rate_limit_count += 1
                print("  🚨 Rate limited")
                # Check rate limit headers if available
                if 'retry-after' in response.headers:
                    print(f"  Retry after: {response.headers['retry-after']}s")
            else:
                print(f"  ❌ Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    print(f"\nSummary:")
    print(f"  Successful requests: {success_count}/5")
    print(f"  Rate limited requests: {rate_limit_count}/5")
    
    return success_count > 0

def main():
    """Run API status tests"""
    print("🚀 Gemini API Status Check")
    print("=" * 50)
    
    # Test 1: Simple API call
    simple_success = test_gemini_api_simple()
    
    # Test 2: Multiple requests (only if first succeeded)
    if simple_success:
        multiple_success = test_multiple_requests()
    else:
        print("\n⚠️  Skipping multiple requests test due to API failure")
        multiple_success = False
    
    print(f"\n{'='*50}")
    print("📊 SUMMARY")
    print("=" * 50)
    
    if simple_success:
        print("✅ Gemini API is accessible")
        if multiple_success:
            print("✅ Multiple requests work (within limits)")
        else:
            print("⚠️  Multiple requests hit rate limits")
    else:
        print("❌ Gemini API is not accessible")
        print("   Possible causes:")
        print("   - API key has hit daily/hourly limits")
        print("   - API key is invalid or restricted")
        print("   - Network connectivity issues")
        print("   - API service is down")
    
    return simple_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)