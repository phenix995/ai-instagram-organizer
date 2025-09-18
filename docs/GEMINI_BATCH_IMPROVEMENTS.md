# Gemini API Batch Processing Improvements

## Overview

The Gemini API batch processing has been significantly improved to handle the strict rate limits of Gemini's free tier (30 requests/second) while maintaining reliability and efficiency.

## Key Improvements

### 1. Gemini-Specific Rate Limiter

- **Conservative Limits**: Designed for Gemini's free tier constraints
  - Max requests/minute: 1500 (vs 30 req/sec = 1800 theoretical max)
  - Max concurrent requests: 3 (vs 25 for Llama)
  - Max requests/second: 25 (buffer below 30 limit)
  - Initial throttle factor: 0.7 (start at 70% capacity)

### 2. Enhanced Circuit Breaker

- **More Sensitive**: Lower failure threshold (3 vs 5 for Llama)
- **Longer Recovery**: 60-second recovery timeout (vs 30 for Llama)
- **Conservative Testing**: Only 2 test calls in half-open state

### 3. Aggressive Backoff Strategy

- **Higher Initial Delay**: 2.0 seconds (vs 1.0 for Llama)
- **Longer Max Delay**: 120 seconds (vs 60 for Llama)
- **Steeper Multiplier**: 2.5x (vs 2.0x for Llama)
- **Jitter**: ±25% randomization to prevent thundering herd

### 4. Intelligent Batch Processing

- **Adaptive Batch Sizes**: 1-3 images per batch (vs 2-8 for Llama)
- **Inter-batch Delays**: 1-10 seconds based on performance
- **Performance Monitoring**: Real-time throttle factor adjustment
- **Circuit-aware Processing**: Single requests when circuit is open

### 5. Conservative Concurrency

- **Low Worker Count**: 3 concurrent workers maximum
- **Extended Timeouts**: 120 seconds for rate-limited requests
- **Progress Monitoring**: Real-time throttle and circuit state display

## Configuration

### Gemini Performance Settings

```json
{
  "gemini": {
    "performance": {
      "max_requests_per_minute": 1500,
      "max_concurrent_requests": 3,
      "adaptive_rate_limiting": true,
      "burst_mode": false,
      "optimal_batch_size": 2,
      "fast_timeout": 60,
      "circuit_breaker": {
        "failure_threshold": 3,
        "recovery_timeout": 60,
        "half_open_max_calls": 2
      },
      "backoff_strategy": {
        "initial_delay": 2.0,
        "max_delay": 120.0,
        "multiplier": 2.5,
        "jitter": true
      }
    }
  }
}
```

## Implementation Details

### Rate Limiter Features

1. **Dual Rate Limiting**: Both per-second and per-minute limits
2. **Adaptive Throttling**: Automatically reduces rate based on errors
3. **Circuit Breaker**: Prevents overwhelming API during outages
4. **Exponential Backoff**: Progressive delays on failures

### Batch Processing Flow

1. **Initialize Rate Limiter**: Create Gemini-specific rate limiter
2. **Adaptive Batching**: Start with small batches, adjust based on performance
3. **Conservative Processing**: Use only 3 concurrent workers
4. **Inter-batch Delays**: Wait between batches based on success rate
5. **Progress Monitoring**: Show throttle factor and circuit state

### Error Handling

- **Rate Limit Errors (429)**: Exponential backoff with jitter
- **API Failures**: Circuit breaker protection
- **Timeout Errors**: Extended timeout handling
- **Network Issues**: Automatic retry with backoff

## Performance Comparison

| Metric | Llama API | Gemini API | Improvement |
|--------|-----------|------------|-------------|
| Max Concurrent | 15 | 3 | 80% reduction |
| Batch Size | 2-8 | 1-3 | Conservative sizing |
| Initial Delay | 1.0s | 2.0s | 100% increase |
| Max Delay | 60s | 120s | 100% increase |
| Failure Threshold | 5 | 3 | 40% reduction |
| Recovery Time | 30s | 60s | 100% increase |

## Usage

### Basic Usage

```python
from instagram_organizer import analyze_images_gemini_optimized, Config

config = Config()
config.ai_provider = 'gemini'

# Process images with improved batch processing
results = analyze_images_gemini_optimized(image_paths, config)
```

### Rate Limiter Usage

```python
from instagram_organizer import GeminiRateLimiter, analyze_single_image_gemini_with_limiter

rate_limiter = GeminiRateLimiter(config)

# Process single image with rate limiting
result = analyze_single_image_gemini_with_limiter(image_path, config, rate_limiter)
```

## Testing

Run the test suite to verify improvements:

```bash
python test_gemini_improvements.py
```

The test suite includes:

- Rate limiter functionality
- Circuit breaker behavior
- Adaptive batch sizing
- Single image analysis
- Batch processing with multiple images

## Monitoring

The improved system provides real-time monitoring:

```
Gemini Analysis: 45%|████▌     | 23/51 [02:15<02:30, 1.12img/s, Success=21, Batch=3/17, Throttle=0.65, Circuit=CLOSED]
```

- **Success**: Number of successfully processed images
- **Batch**: Current batch number and total batches
- **Throttle**: Current throttle factor (1.0 = full speed, lower = throttled)
- **Circuit**: Circuit breaker state (CLOSED/OPEN/HALF_OPEN)

## Troubleshooting

### Common Issues

1. **"Circuit breaker OPEN"**: API is experiencing issues, wait for recovery
2. **"Rate limit hit"**: Normal behavior, system will automatically backoff
3. **"Throttle factor low"**: System detected errors, reducing request rate
4. **Slow processing**: Expected with conservative settings, ensures reliability

### Performance Tuning

For paid Gemini accounts with higher limits, adjust these settings:

```json
{
  "gemini": {
    "performance": {
      "max_requests_per_minute": 6000,
      "max_concurrent_requests": 10,
      "max_requests_per_second": 100,
      "optimal_batch_size": 5
    }
  }
}
```

## Benefits

1. **Reliability**: Significantly reduced 429 errors
2. **Efficiency**: Optimal use of free tier limits
3. **Resilience**: Circuit breaker prevents API overload
4. **Adaptability**: Automatic adjustment to API performance
5. **Monitoring**: Real-time visibility into processing state

## Migration from Old System

The improvements are backward compatible. Simply update your code to use:

- `analyze_images_gemini_optimized()` instead of the old function
- `GeminiRateLimiter` for advanced rate limiting
- Updated configuration with Gemini performance settings

The system will automatically use the improved batch processing with conservative defaults suitable for Gemini's free tier.
