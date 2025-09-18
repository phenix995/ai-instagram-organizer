#!/usr/bin/env python3
"""
Debug script to reproduce Llama API errors
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

def test_single_image_analysis():
    """Test the exact payload used in the organizer for image analysis"""
    
    api_key = "***REMOVED_LLAMA_API_KEY***"
    
    # Use the test image
    test_image = "test_image_complex.jpg"
    if not os.path.exists(test_image):
        print("❌ Test image not found")
        return False
    
    base64_image = image_to_base64(test_image)
    
    # Use the exact prompt from the organizer
    prompt_text = """Analyze this image for Instagram and return ONLY a JSON object with these exact fields:

{
  "technical_score": 7,
  "visual_appeal": 8,
  "engagement_score": 6,
  "uniqueness": 5,
  "story_potential": 7,
  "category": "portrait",
  "subcategory": "casual_portrait",
  "location": "outdoor setting with mountains",
  "mood": "peaceful",
  "strengths": ["good lighting", "nice composition"],
  "weaknesses": ["slightly blurry"],
  "best_time": "afternoon",
  "caption_style": "casual",
  "hashtag_focus": "lifestyle",
  "people_present": "1",
  "time_of_day_indicators": "natural daylight"
}

Rate technical_score, visual_appeal, engagement_score, uniqueness, and story_potential from 1-10.
Choose category from: landscape, portrait, food, architecture, lifestyle, travel, nature, street, action.
Return ONLY valid JSON, no markdown formatting."""
    
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
                        "text": prompt_text
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
    
    print("🔍 Testing single image analysis with organizer payload...")
    print(f"📏 Payload size: {len(json.dumps(payload))} bytes")
    print(f"📏 Base64 image size: {len(base64_image)} bytes")
    
    try:
        response = requests.post(
            "https://api.llama.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis request successful")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_content_generation():
    """Test content generation with multiple images"""
    
    api_key = "***REMOVED_LLAMA_API_KEY***"
    
    # Use the test image multiple times to simulate batch
    test_image = "test_image_complex.jpg"
    if not os.path.exists(test_image):
        print("❌ Test image not found")
        return False
    
    base64_image = image_to_base64(test_image)
    
    # Test with 9 images (Llama API limit)
    base64_images = [base64_image] * 9  # 9 copies of the same image
    
    prompt_text = """You are a creative social media manager. Looking at these images, generate a JSON object with these exact keys:
    1. "caption_options": A list of 3 different, engaging Instagram caption ideas
    2. "hashtags": A list of 15-20 relevant hashtags without the # symbol
    3. "post_theme": A brief description of the overall theme
    
    Return ONLY the JSON object, no other text."""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Build content array with text and images
    content = [
        {
            "type": "text",
            "text": prompt_text
        }
    ]
    
    for base64_img in base64_images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img}"
            }
        })
    
    payload = {
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }
    
    print("🎨 Testing content generation with multiple images...")
    print(f"📏 Payload size: {len(json.dumps(payload))} bytes")
    print(f"📏 Number of images: {len(base64_images)}")
    
    try:
        response = requests.post(
            "https://api.llama.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Content generation successful")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🐛 Debugging Llama API Errors")
    print("=" * 40)
    
    print("\n1. Testing single image analysis...")
    test_single_image_analysis()
    
    print("\n2. Testing content generation with multiple images...")
    test_content_generation()