#!/usr/bin/env python3
"""
Test script for rate limiting improvements
"""

import time
from ai_instagram_organizer import Config

def test_rate_limiting():
    """Test the improved rate limiting configuration"""
    
    print("🚦 Rate Limiting Configuration Test")
    print("=" * 50)
    
    # Load config
    config = Config()
    
    print(f"📊 Current AI Analysis Settings:")
    print(f"   - Parallel workers: {config.ai_parallel_workers}")
    print(f"   - Batch size: {config.ai_batch_size}")
    print(f"   - Max retries: {config.ai_max_retries}")
    print(f"   - Timeout: {config.ai_timeout}s")
    
    # Calculate expected processing time
    total_photos = 100  # Example
    batches = (total_photos + config.ai_batch_size - 1) // config.ai_batch_size
    
    # Estimate time with rate limiting
    base_time_per_batch = 3.0  # seconds (API call + processing)
    retry_overhead = 2.0  # seconds (average retry delay)
    batch_delay = 2.0  # seconds between batches
    
    estimated_time = (batches * base_time_per_batch) + ((batches - 1) * batch_delay)
    estimated_time_with_retries = estimated_time + (batches * 0.3 * retry_overhead)  # 30% retry rate
    
    print(f"\n⏱️  Processing Time Estimates (for {total_photos} photos):")
    print(f"   - Number of batches: {batches}")
    print(f"   - Estimated time (no retries): {estimated_time/60:.1f} minutes")
    print(f"   - Estimated time (with retries): {estimated_time_with_retries/60:.1f} minutes")
    
    print(f"\n💡 Rate Limiting Benefits:")
    print(f"   - Reduces 429 rate limit errors")
    print(f"   - Exponential backoff prevents API blocking")
    print(f"   - Smaller batch sizes are more reliable")
    print(f"   - Delays between batches respect API limits")
    
    print(f"\n⚙️  Recommended Settings by Use Case:")
    print(f"   - Small collections (<50 photos): batch_size=8, workers=10")
    print(f"   - Medium collections (50-200 photos): batch_size=4, workers=5")
    print(f"   - Large collections (200+ photos): batch_size=2, workers=3")
    
    print(f"\n🔧 Configuration Tips:")
    print(f"   - Lower batch_size = more reliable but slower")
    print(f"   - Higher max_retries = better success rate")
    print(f"   - Longer timeout = handles slow responses")
    print(f"   - Enable caching to avoid re-analyzing same photos")

if __name__ == "__main__":
    test_rate_limiting()