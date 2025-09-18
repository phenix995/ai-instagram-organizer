#!/usr/bin/env python3
"""
Performance test for Llama API optimizations
"""

import os
import time
import json
from pathlib import Path
from ai_instagram_organizer import Config, analyze_images_parallel, LlamaRateLimiter

def create_test_images(count: int = 10):
    """Create test images for performance testing"""
    from PIL import Image, ImageDraw
    import random
    
    test_images = []
    
    for i in range(count):
        # Create varied test images
        img = Image.new('RGB', (1200, 800), color=(
            random.randint(50, 200),
            random.randint(50, 200), 
            random.randint(50, 200)
        ))
        
        draw = ImageDraw.Draw(img)
        
        # Add random content to make each image unique
        for j in range(20):
            x1, y1 = random.randint(0, 1100), random.randint(0, 700)
            x2, y2 = x1 + random.randint(50, 100), y1 + random.randint(50, 100)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            draw.rectangle([x1, y1, x2, y2], fill=color)
        
        filename = f'perf_test_image_{i:03d}.jpg'
        img.save(filename, quality=95)
        test_images.append(filename)
        
    return test_images

def test_llama_performance():
    """Test Llama API performance with different configurations"""
    
    print("🚀 Llama API Performance Test")
    print("=" * 50)
    
    # Check API key
    if not os.environ.get('LLAMA_API_KEY'):
        print("❌ LLAMA_API_KEY not set. Using config file key.")
    
    # Create test images
    print("📸 Creating test images...")
    test_images = create_test_images(15)
    print(f"✅ Created {len(test_images)} test images")
    
    # Test configurations
    test_configs = [
        {
            "name": "Conservative (Original)",
            "parallel_workers": 2,
            "batch_size": 1,
            "rate_limit_delay": 5.0
        },
        {
            "name": "Optimized (New)",
            "parallel_workers": 25,
            "batch_size": 5,
            "rate_limit_delay": 0.5
        },
        {
            "name": "High Throughput",
            "parallel_workers": 50,
            "batch_size": 8,
            "rate_limit_delay": 0.2
        }
    ]
    
    results = []
    
    for test_config in test_configs:
        print(f"\n🧪 Testing: {test_config['name']}")
        print(f"   Workers: {test_config['parallel_workers']}")
        print(f"   Batch size: {test_config['batch_size']}")
        print(f"   Rate limit delay: {test_config['rate_limit_delay']}s")
        
        # Update config
        config = Config()
        config.ai_provider = 'llama'
        config.ai_parallel_workers = test_config['parallel_workers']
        config.ai_batch_size = test_config['batch_size']
        config.rate_limit_delay = test_config['rate_limit_delay']
        config.enable_fast_mode = False  # Disable pre-filtering for fair comparison
        
        # Run test
        start_time = time.time()
        
        try:
            analyzed_results = analyze_images_parallel(test_images[:10], config)  # Test with 10 images
            end_time = time.time()
            
            duration = end_time - start_time
            success_count = len(analyzed_results)
            success_rate = success_count / 10 * 100
            throughput = success_count / duration if duration > 0 else 0
            
            result = {
                'config': test_config['name'],
                'duration': duration,
                'success_count': success_count,
                'success_rate': success_rate,
                'throughput': throughput,
                'avg_quality': sum(r['analysis'].get('composite_score', 0) for r in analyzed_results) / len(analyzed_results) if analyzed_results else 0
            }
            
            results.append(result)
            
            print(f"   ✅ Duration: {duration:.1f}s")
            print(f"   ✅ Success: {success_count}/10 ({success_rate:.1f}%)")
            print(f"   ✅ Throughput: {throughput:.2f} images/sec")
            print(f"   ✅ Avg Quality: {result['avg_quality']:.1f}/10")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append({
                'config': test_config['name'],
                'error': str(e)
            })
        
        # Cool down between tests
        time.sleep(2)
    
    # Print summary
    print("\n📊 Performance Summary")
    print("=" * 50)
    
    for result in results:
        if 'error' not in result:
            print(f"{result['config']:20} | {result['duration']:6.1f}s | {result['throughput']:6.2f} img/s | {result['success_rate']:6.1f}%")
        else:
            print(f"{result['config']:20} | ERROR: {result['error']}")
    
    # Find best performer
    valid_results = [r for r in results if 'error' not in r and r['success_rate'] > 80]
    if valid_results:
        best = max(valid_results, key=lambda x: x['throughput'])
        print(f"\n🏆 Best Performance: {best['config']}")
        print(f"   Throughput: {best['throughput']:.2f} images/sec")
        print(f"   Duration: {best['duration']:.1f}s for 10 images")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test images...")
    for img in test_images:
        try:
            os.remove(img)
        except:
            pass
    
    print("✅ Performance test complete!")

def test_rate_limiter():
    """Test the rate limiter functionality"""
    print("\n🔧 Testing Rate Limiter")
    print("-" * 30)
    
    config = Config()
    config.ai_provider = 'llama'
    
    rate_limiter = LlamaRateLimiter(config)
    
    print(f"Max requests/minute: {rate_limiter.max_requests_per_minute}")
    print(f"Max concurrent: {rate_limiter.max_concurrent}")
    print(f"Adaptive limiting: {rate_limiter.adaptive_rate_limiting}")
    print(f"Burst mode: {rate_limiter.burst_mode}")
    
    # Test rate limiting
    print("\n🧪 Testing rate limiting logic...")
    
    start_time = time.time()
    requests_made = 0
    
    # Simulate rapid requests
    for i in range(20):
        if rate_limiter.can_make_request():
            rate_limiter.acquire()
            requests_made += 1
            # Simulate successful request
            time.sleep(0.1)
            rate_limiter.release(success=True)
        else:
            wait_time = rate_limiter.wait_for_slot()
            print(f"   Rate limit hit, would wait {wait_time:.2f}s")
            break
    
    duration = time.time() - start_time
    print(f"✅ Made {requests_made} requests in {duration:.2f}s")
    print(f"✅ Throttle factor: {rate_limiter.throttle_factor:.2f}")

if __name__ == "__main__":
    test_llama_performance()
    test_rate_limiter()