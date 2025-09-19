#!/usr/bin/env python3
"""
Test script to see what Gemini is actually returning
"""

import os
import requests
import json
import base64
from PIL import Image
from io import BytesIO

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def test_gemini_simple():
    """Test Gemini with a simple prompt"""
    
    # Use a simple test image path - adjust this to an actual image
    image_path = "test_image_complex.jpg"
    
    try:
        base64_image = encode_image_to_base64(image_path)
    except Exception as e:
        print(f"Error encoding image: {e}")
        return
    
    # Simple prompt first
    simple_prompt = """Analyze this image for Instagram and return ONLY a JSON object with these exact fields:

{
  "technical_score": 7,
  "visual_appeal": 8,
  "engagement_score": 6,
  "uniqueness": 5,
  "story_potential": 7,
  "category": "portrait",
  "location": "outdoor setting with mountains",
  "mood": "peaceful"
}

Rate technical_score, visual_appeal, engagement_score, uniqueness, and story_potential from 1-10.
Choose category from: landscape, portrait, food, architecture, lifestyle, travel, nature, street, action.
Return ONLY valid JSON, no markdown formatting."""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Error: API key is not set.")
        return False
    
    model = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": simple_prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    try:
        print("Sending request to Gemini...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        print("Raw Gemini Response:")
        print(json.dumps(response_data, indent=2))
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            content = response_data['candidates'][0]['content']['parts'][0]['text']
            print(f"\nExtracted Content:")
            print(content)
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print(f"\nSuccessfully parsed JSON:")
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as e:
                print(f"\nFailed to parse as JSON: {e}")
                print("Trying to clean up the response...")
                
                # Clean up response
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    parsed = json.loads(content)
                    print(f"Successfully parsed cleaned JSON:")
                    print(json.dumps(parsed, indent=2))
                except json.JSONDecodeError as e2:
                    print(f"Still failed to parse: {e2}")
                    print(f"Cleaned content: {content}")
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")

if __name__ == "__main__":
    test_gemini_simple()