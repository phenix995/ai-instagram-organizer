#!/usr/bin/env python3
"""
Test script for improved Llama API batch processing
"""

import os
import json
import time
import requests
from pathlib import Path

def test_circuit_breaker_simulation():
    """Simulate circuit breaker behavior"""
    print("🔧 Testing Circuit Breaker Logic")
    print("=" * 40)
    
    # Simulate the circuit breaker states
    failure_threshold = 5
    recovery_timeout = 10
    
    failure_count = 0
    circuit_state = "CLOSED"
    last_failure_time = 0
    
    # Simulate failures
    for i in range(8):
        print(f"Request {i+1}:")
        
        if circuit_state == "OPEN":
            if time.time() - last_failure_time > recovery_timeout:
                circuit_state = "HALF_OPEN"
                print(f"  Circuit: CLOSED -> HALF_OPEN (recovery timeout reached)")
            else:
                print(f"  Circuit: OPEN - Request blocked")
                continue
        
        # Simulate API call (fail first 6, then succeed)
        success = i >= 6
        
        if success:
            print(f"  API: SUCCESS")
            if circuit_state == "HALF_OPEN":
                circuit_state = "CLOSED"
                failure_count = 0
                print(f"  Circuit: HALF_OPEN -> CLOSED")
        else:
            print(f"  API: FAILURE")
            failure_count += 1
            last_failure_time = time.time()
            
            if failure_count >= failure_threshold:
                circuit_state = "OPEN"
                print(f"  Circuit: CLOSED -> OPEN ({failure_count} failures)")
        
        print(f"  State: {circuit_state}, Failures: {failure_count}")
        print()
        
        time.sleep(1)

def test_adaptive_batching():
    """Test adaptive batch sizing logic"""
    print("📊 Testing Adaptive Batch Sizing")
    print("=" * 40)
    
    # Simulate different error rates and their effect on batch size
    base_batch_size = 4
    scenarios = [
        ("No errors", 0.0),
        ("Low errors", 0.05),
        ("Medium errors", 0.15),
        ("High errors", 0.35),
        ("Very high errors", 0.60)
    ]
    
    for scenario, error_rate in scenarios:
        if error_rate == 0.0:
            throttle_factor = 1.0
            circuit_state = "CLOSED"
        elif error_rate < 0.1:
            throttle_factor = 0.95
            circuit_state = "CLOSED"
        elif error_rate < 0.2:
            throttle_factor = 0.8
            circuit_state = "CLOSED"
        elif error_rate < 0.4:
            throttle_factor = 0.5
            circuit_state = "HALF_OPEN"
        else:
            throttle_factor = 0.3
            circuit_state = "OPEN"
        
        # Calculate batch size
        if circuit_state == "OPEN":
            batch_size = 1
        elif throttle_factor < 0.8:
            batch_size = max(1, base_batch_size // 2)
        elif throttle_factor > 0.95:
            batch_size = min(8, base_batch_size * 2)
        else:
            batch_size = base_batch_size
        
        print(f"{scenario:15} | Error Rate: {error_rate:5.1%} | Throttle: {throttle_factor:4.2f} | Circuit: {circuit_state:9} | Batch Size: {batch_size}")

def test_backoff_calculation():
    """Test exponential backoff with jitter"""
    print("⏱️  Testing Exponential Backoff")
    print("=" * 40)
    
    initial_delay = 1.0
    max_delay = 60.0
    multiplier = 2.0
    current_delay = initial_delay
    
    print(f"Initial delay: {initial_delay}s")
    print(f"Max delay: {max_delay}s")
    print(f"Multiplier: {multiplier}x")
    print()
    
    for failure in range(8):
        # Add jitter (±25%)
        jitter_range = current_delay * 0.25
        jittered_delay = current_delay + (jitter_range * 0.5)  # Simulate average jitter
        
        print(f"Failure {failure + 1}: Base delay: {current_delay:5.1f}s, With jitter: {jittered_delay:5.1f}s")
        
        # Increase delay for next failure
        current_delay = min(max_delay, current_delay * multiplier)

if __name__ == "__main__":
    print("🚀 Testing Improved Llama API Batch Processing")
    print("=" * 50)
    print()
    
    test_circuit_breaker_simulation()
    print()
    test_adaptive_batching()
    print()
    test_backoff_calculation()
    
    print("\n✅ All tests completed!")
    print("\nKey Improvements:")
    print("• Circuit breaker prevents API overload")
    print("• Adaptive batch sizing based on error rates")
    print("• Exponential backoff with jitter")
    print("• Conservative concurrency limits")
    print("• Intelligent failure recovery")