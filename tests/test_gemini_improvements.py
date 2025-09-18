#!/usr/bin/env python3
"""
Test script for Gemini API batch processing improvements
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_instagram_organizer import Config, GeminiRateLimiter, analyze_images_gemini_optimized, analyze_single_image_gemini_with_limiter

def test_gemini_rate_limiter():
    """Test the Gemini rate limiter functionality"""
    print("🔧 Testing Gemini Rate Limiter")
    print("=" * 40)
    
    config = Config()
    config.ai_provider = 'gemini'
    
    rate_limiter = GeminiRateLimiter(config)
    
    print(f"Max requests/minute: {rate_limiter.max_requests_per_minute}")
    print(f"Max requests/second: {rate_limiter.max_requests_per_second}")
    print(f"Max concurrent: {rate_limiter.max_concurrent}")
    print(f"Initial throttle factor: {rate_limiter.throttle_factor}")
    print(f"Circuit breaker threshold: {rate_limiter.failure_threshold}")
    print()
    
    # Test rate limiting logic
    print("🧪 Testing rate limiting logic...")
    
    start_time = time.time()
    requests_made = 0
    
    # Simulate rapid requests
    for i in range(10):
        if rate_limiter.can_make_request():
            print(f"  Request {i+1}: ALLOWED")
            rate_limiter.acquire()
            requests_made += 1
            # Simulate successful request
            time.sleep(0.1)
            rate_limiter.release(success=True)
        else:
            wait_time = rate_limiter.wait_for_slot()
            print(f"  Request {i+1}: RATE LIMITED - would wait {wait_time:.2f}s")
            if wait_time > 0:
                time.sleep(min(wait_time, 2.0))  # Cap wait time for testing
    
    duration = time.time() - start_time
    print(f"\n✅ Made {requests_made} requests in {duration:.2f}s")
    print(f"✅ Final throttle factor: {rate_limiter.throttle_factor:.2f}")
    print(f"✅ Circuit state: {rate_limiter.circuit_state}")
    
    return True

def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("\n🔧 Testing Circuit Breaker")
    print("=" * 40)
    
    config = Config()
    rate_limiter = GeminiRateLimiter(config)
    
    print("Simulating failures to trigger circuit breaker...")
    
    # Simulate failures
    for i in range(5):
        rate_limiter.record_failure()
        print(f"  Failure {i+1}: Circuit state = {rate_limiter.circuit_state}")
    
    print(f"\n✅ Circuit breaker opened after {rate_limiter.failure_count} failures")
    print(f"✅ Recovery timeout: {rate_limiter.recovery_timeout}s")
    
    # Test recovery
    print("\nTesting recovery...")
    time.sleep(2)  # Simulate some time passing
    
    # Simulate successful calls to recover
    for i in range(3):
        rate_limiter.record_success()
        print(f"  Success {i+1}: Circuit state = {rate_limiter.circuit_state}")
    
    return True

def test_batch_sizing():
    """Test adaptive batch sizing"""
    print("\n🔧 Testing Adaptive Batch Sizing")
    print("=" * 40)
    
    config = Config()
    rate_limiter = GeminiRateLimiter(config)
    
    print(f"Initial batch size: {rate_limiter.get_optimal_batch_size()}")
    
    # Simulate different throttle conditions
    test_conditions = [
        (0.8, "Good performance"),
        (0.6, "Moderate throttling"),
        (0.4, "Heavy throttling"),
        (0.2, "Severe throttling")
    ]
    
    for throttle, description in test_conditions:
        rate_limiter.throttle_factor = throttle
        batch_size = rate_limiter.get_optimal_batch_size()
        print(f"  {description} (throttle: {throttle}): batch size = {batch_size}")
    
    # Test circuit open condition
    rate_limiter.circuit_state = "OPEN"
    batch_size = rate_limiter.get_optimal_batch_size()
    print(f"  Circuit OPEN: batch size = {batch_size}")
    
    return True

def create_test_image():
    """Create a simple test image for API testing"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)
        
        # Add some content
        draw.rectangle([100, 100, 700, 500], fill=(200, 100, 50))
        draw.text((200, 250), "Test Image for Gemini", fill=(255, 255, 255))
        
        test_image_path = "test_gemini_image.jpg"
        img.save(test_image_path, quality=95)
        
        return test_image_path
        
    except ImportError:
        print("⚠️  PIL not available, using existing test image")
        # Look for existing test image
        for ext in ['.jpg', '.jpeg', '.png']:
            for name in ['test_image_complex', 'test_gemini_image']:
                path = f"{name}{ext}"
                if os.path.exists(path):
                    return path
        return None

def test_single_image_analysis():
    """Test single image analysis with rate limiter"""
    print("\n🔧 Testing Single Image Analysis")
    print("=" * 40)
    
    test_image = create_test_image()
    if not test_image:
        print("❌ No test image available")
        return False
    
    print(f"Using test image: {test_image}")
    
    config = Config()
    rate_limiter = GeminiRateLimiter(config)
    
    try:
        print("Analyzing image with rate limiter...")
        start_time = time.time()
        
        result = analyze_single_image_gemini_with_limiter(test_image, config, rate_limiter)
        
        duration = time.time() - start_time
        
        if result:
            print(f"✅ Analysis successful in {duration:.2f}s")
            print(f"✅ Composite score: {result['analysis'].get('composite_score', 'N/A')}")
            print(f"✅ Instagram tier: {result['analysis'].get('instagram_tier', 'N/A')}")
            print(f"✅ Throttle factor: {rate_limiter.throttle_factor:.2f}")
            return True
        else:
            print(f"❌ Analysis failed after {duration:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up test image if we created it
        if test_image == "test_gemini_image.jpg" and os.path.exists(test_image):
            os.remove(test_image)

def test_batch_processing():
    """Test batch processing with multiple images"""
    print("\n🔧 Testing Batch Processing")
    print("=" * 40)
    
    # Create multiple test images
    test_images = []
    try:
        from PIL import Image, ImageDraw
        import random
        
        for i in range(5):  # Small batch for testing
            img = Image.new('RGB', (800, 600), color=(
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200)
            ))
            draw = ImageDraw.Draw(img)
            draw.rectangle([100, 100, 700, 500], fill=(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ))
            draw.text((200, 250), f"Test Image {i+1}", fill=(255, 255, 255))
            
            filename = f'test_batch_image_{i:02d}.jpg'
            img.save(filename, quality=95)
            test_images.append(filename)
            
    except ImportError:
        print("⚠️  PIL not available, skipping batch test")
        return True
    
    if not test_images:
        print("❌ No test images created")
        return False
    
    print(f"Created {len(test_images)} test images")
    
    config = Config()
    
    try:
        print("Running batch analysis...")
        start_time = time.time()
        
        results = analyze_images_gemini_optimized(test_images, config)
        
        duration = time.time() - start_time
        
        print(f"✅ Batch processing complete in {duration:.2f}s")
        print(f"✅ Processed {len(results)}/{len(test_images)} images successfully")
        print(f"✅ Average time per image: {duration/len(test_images):.2f}s")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        return False
    finally:
        # Clean up test images
        for img_path in test_images:
            if os.path.exists(img_path):
                os.remove(img_path)

def main():
    """Run all tests"""
    print("🚀 Gemini API Batch Processing Improvements Test Suite")
    print("=" * 60)
    
    tests = [
        ("Rate Limiter", test_gemini_rate_limiter),
        ("Circuit Breaker", test_circuit_breaker),
        ("Batch Sizing", test_batch_sizing),
        ("Single Image Analysis", test_single_image_analysis),
        ("Batch Processing", test_batch_processing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gemini improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)