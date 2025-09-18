#!/usr/bin/env python3
"""
==================================================
AI Instagram Photos Organizer
==================================================
AI-powered tool to organize photos into Instagram-ready posts with smart captions and hashtags.
Supports both Ollama (local) and Gemini (cloud) AI providers.
==================================================
MIT License
Copyright (c) 2025 Summit Singh Thakur
==================================================
"""

import os
import base64
import json
import time
import random
import requests
import shutil
import random
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO
import datetime
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
import hashlib
import threading
from functools import lru_cache
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import tqdm for progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.warning("tqdm not available. Install with: pip install tqdm")

# Check for required dependencies
try:
    import imagehash
except ImportError:
    logger.error("'imagehash' is not installed. Please run: pip install imagehash")
    exit(1)

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    logger.info("HEIC/HEIF support enabled")
except ImportError:
    logger.warning("'pillow-heif' not installed. HEIC/HEIF conversion may fail.")

# Optional advanced features
ADVANCED_FEATURES = {}
try:
    from features.analytics import analyze_photo_patterns, generate_analytics_report, create_analytics_visualizations
    ADVANCED_FEATURES['analytics'] = True
except ImportError:
    ADVANCED_FEATURES['analytics'] = False

try:
    from features.hashtag_intelligence import HashtagOptimizer
    ADVANCED_FEATURES['hashtag_optimizer'] = True
except ImportError:
    ADVANCED_FEATURES['hashtag_optimizer'] = False

try:
    from features.multi_platform import create_platform_variants
    ADVANCED_FEATURES['multi_platform'] = True
except ImportError:
    ADVANCED_FEATURES['multi_platform'] = False

try:
    from features.scheduling import generate_posting_schedule
    ADVANCED_FEATURES['scheduling'] = True
except ImportError:
    ADVANCED_FEATURES['scheduling'] = False

try:
    from features.image_enhancement import auto_enhance_image
    ADVANCED_FEATURES['image_enhancement'] = True
except ImportError:
    ADVANCED_FEATURES['image_enhancement'] = False

# Constants
SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.heic', '.heif')
CONVERTED_FORMATS = ('.png', '.jpg', '.jpeg')
THUMBNAIL_SIZE = (1024, 1024)

# Global cache for AI analysis results
_analysis_cache = {}
_cache_lock = threading.Lock()

# Global rate limiter instance will be defined after Config class
_llama_rate_limiter = None

def get_image_hash_for_cache(image_path: str) -> str:
    """Generate a hash for caching based on file path and modification time"""
    stat = os.stat(image_path)
    cache_key = f"{image_path}_{stat.st_mtime}_{stat.st_size}"
    return hashlib.md5(cache_key.encode()).hexdigest()

class Config:
    """Configuration manager for Instagram photo organizer"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self._setup_attributes()
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from file or create default"""
        default_config = {
            "source_folder": "source_photos",
            "output_folder_prefix": "instagram_posts",
            "temp_convert_folder": "temp_converted_images",
            "ai_provider": "llama",
            "processing": {
                "post_size": 10,
                "process_all": True,
                "dev_mode_limit": 100,
                "similarity_threshold": 3,
                "image_quality": 95,
                "similarity_optimization": {
                    "parallel_workers": 4,
                    "thumbnail_size": 256,
                    "hash_size": 8,
                    "batch_size": 100,
                    "enable_prefilter": True
                }
            },
            "llama": {
                "api_key": "",
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "api_url": "https://api.llama.com/v1/chat/completions",
                "timeout": 120
            },
            "ollama": {
                "api_url": "http://localhost:11434/api/generate",
                "model": "gemma3:4b",
                "timeout": 120
            },
            "gemini": {
                "api_key": "",
                "model": "gemini-1.5-flash",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models"
            },
            "features": {
                "enable_enhancement": True,
                "enable_analytics": True,
                "enable_scheduling": True,
                "enable_multi_platform": True,
                "enable_hashtag_optimization": True
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    self._deep_update(default_config, file_config)
                logger.info(f"Loaded config from {config_file}")
            except Exception as e:
                logger.warning(f"Could not load config file {config_file}: {e}")
        else:
            logger.info(f"Config file {config_file} not found, using defaults")
        
        return default_config
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Deep merge dictionaries"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _setup_attributes(self):
        """Setup config attributes for easy access"""
        self.source_folder = self.config["source_folder"]
        self.output_folder = f"{self.config['output_folder_prefix']}_{int(time.time())}"
        self.temp_convert_folder = self.config["temp_convert_folder"]
        self.ai_provider = self.config["ai_provider"]
        
        # Processing settings
        proc = self.config["processing"]
        self.post_size = proc["post_size"]
        self.process_all = proc["process_all"]
        self.dev_mode_limit = proc["dev_mode_limit"]
        self.similarity_threshold = proc["similarity_threshold"]
        self.image_quality = proc["image_quality"]
        self.keep_temp_files = proc.get("keep_temp_files", False)
        
        # Similarity optimization settings
        sim_opt = proc.get("similarity_optimization", {})
        self.parallel_workers = sim_opt.get("parallel_workers", 4)
        self.thumbnail_size = sim_opt.get("thumbnail_size", 256)
        self.hash_size = sim_opt.get("hash_size", 8)
        self.batch_size = sim_opt.get("batch_size", 100)
        self.enable_prefilter = sim_opt.get("enable_prefilter", True)
        
        # AI provider settings
        self.ollama = self.config["ollama"]
        self.gemini = self.config["gemini"]
        self.llama = self.config.get("llama", {})
        
        # Feature flags (only enable if modules are available)
        features = self.config["features"]
        self.enable_enhancement = features["enable_enhancement"] and ADVANCED_FEATURES.get('image_enhancement', False)
        self.enable_analytics = features["enable_analytics"] and ADVANCED_FEATURES.get('analytics', False)
        self.enable_scheduling = features["enable_scheduling"] and ADVANCED_FEATURES.get('scheduling', False)
        self.enable_multi_platform = features["enable_multi_platform"] and ADVANCED_FEATURES.get('multi_platform', False)
        self.enable_hashtag_optimization = features["enable_hashtag_optimization"] and ADVANCED_FEATURES.get('hashtag_optimizer', False)
        
        # Performance settings
        perf = self.config.get("performance", {})
        ai_perf = perf.get("ai_analysis", {})
        img_perf = perf.get("image_processing", {})
        
        self.ai_parallel_workers = ai_perf.get("parallel_workers", 10)
        self.ai_batch_size = ai_perf.get("batch_size", 8)
        self.ai_max_retries = ai_perf.get("max_retries", 3)
        self.ai_timeout = ai_perf.get("timeout", 30)
        self.enable_caching = ai_perf.get("enable_caching", True)
        self.cache_duration_hours = ai_perf.get("cache_duration_hours", 24)
        
        self.fast_thumbnail_size = img_perf.get("thumbnail_size", 512)
        self.fast_jpeg_quality = img_perf.get("jpeg_quality", 85)
        self.enable_fast_mode = img_perf.get("enable_fast_mode", True)
        
        # Contextual filtering settings
        ctx_filter = self.config.get("contextual_filtering", {})
        self.enable_contextual_filtering = ctx_filter.get("enable_contextual_filtering", True)
        self.contextual_similarity_threshold = ctx_filter.get("contextual_similarity_threshold", 0.7)
        self.contextual_selection_strategy = ctx_filter.get("contextual_selection_strategy", "highest_score")
        self.max_photos_per_context = ctx_filter.get("max_photos_per_context", 3)
        self.min_resolution = img_perf.get("min_resolution", [800, 600])
        self.min_file_size_kb = img_perf.get("min_file_size_kb", 100)
    
    def update_from_args(self, args):
        """Update config from command line arguments"""
        if args.source:
            self.source_folder = args.source
        if args.output:
            self.output_folder = f"{args.output}_{int(time.time())}"
        if args.dev_mode:
            self.process_all = False
        if args.limit:
            self.dev_mode_limit = args.limit
        if args.post_size:
            self.post_size = args.post_size
        if args.similarity is not None:
            self.similarity_threshold = args.similarity
        if args.ai_provider:
            self.ai_provider = args.ai_provider
        if args.llama_key:
            self.llama["api_key"] = args.llama_key
        if args.gemini_key:
            self.gemini["api_key"] = args.gemini_key
        if args.ollama_url:
            self.ollama["api_url"] = args.ollama_url
        if args.ollama_model:
            self.ollama["model"] = args.ollama_model
        if args.simple_mode:
            # Disable advanced features in simple mode
            self.enable_enhancement = False
            self.enable_analytics = False
            self.enable_scheduling = False
            self.enable_multi_platform = False
            self.enable_hashtag_optimization = False
        
        # Performance overrides
        if args.parallel_workers:
            self.ai_parallel_workers = args.parallel_workers
        if args.batch_size:
            self.ai_batch_size = args.batch_size
        if args.fast_mode:
            self.enable_fast_mode = True
        if args.no_cache:
            self.enable_caching = False
        
        # Contextual filtering overrides
        if args.no_contextual_filter:
            self.enable_contextual_filtering = False
        if args.contextual_threshold:
            self.contextual_similarity_threshold = args.contextual_threshold

class GeminiRateLimiter:
    """Conservative rate limiter for Gemini API with strict rate limiting"""
    
    def __init__(self, config: Config):
        self.config = config
        gemini_perf = config.gemini.get('performance', {}) if hasattr(config, 'gemini') else {}
        
        # Gemini free tier: 30 requests/second = 1800 requests/minute
        self.max_requests_per_minute = gemini_perf.get('max_requests_per_minute', 1500)  # Conservative
        self.max_concurrent = gemini_perf.get('max_concurrent_requests', 3)  # Very conservative
        self.adaptive_rate_limiting = gemini_perf.get('adaptive_rate_limiting', True)
        
        # Circuit breaker configuration - more sensitive for Gemini
        cb_config = gemini_perf.get('circuit_breaker', {})
        self.failure_threshold = cb_config.get('failure_threshold', 3)  # Lower threshold
        self.recovery_timeout = cb_config.get('recovery_timeout', 60)  # Longer recovery
        self.half_open_max_calls = cb_config.get('half_open_max_calls', 2)
        
        # Backoff strategy - more aggressive for Gemini
        backoff_config = gemini_perf.get('backoff_strategy', {})
        self.initial_delay = backoff_config.get('initial_delay', 2.0)  # Start with longer delay
        self.max_delay = backoff_config.get('max_delay', 120.0)  # Longer max delay
        self.multiplier = backoff_config.get('multiplier', 2.5)  # More aggressive backoff
        self.jitter = backoff_config.get('jitter', True)
        
        # Rate limiting state
        self.request_times = deque()
        self.concurrent_requests = 0
        self.lock = threading.Lock()
        self.semaphore = threading.Semaphore(self.max_concurrent)
        
        # Adaptive throttling - start more conservative
        self.success_rate = 1.0
        self.recent_errors = deque()
        self.throttle_factor = 0.7  # Start at 70% capacity
        self.current_delay = self.initial_delay
        
        # Circuit breaker state
        self.circuit_state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        # Gemini-specific: Track requests per second
        self.requests_this_second = deque()
        self.max_requests_per_second = 25  # Conservative limit for free tier
        
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while self.request_times and now - self.request_times[0] > 60:
                self.request_times.popleft()
            
            # Remove requests older than 1 second
            while self.requests_this_second and now - self.requests_this_second[0] > 1:
                self.requests_this_second.popleft()
            
            # Check per-second limit first (most restrictive for Gemini)
            if len(self.requests_this_second) >= self.max_requests_per_second:
                return False
            
            # Apply adaptive throttling to per-minute limit
            effective_limit = int(self.max_requests_per_minute * self.throttle_factor)
            
            return len(self.request_times) < effective_limit
    
    def wait_for_slot(self) -> float:
        """Calculate how long to wait for the next available slot"""
        with self.lock:
            now = time.time()
            
            # Check per-second limit first
            while self.requests_this_second and now - self.requests_this_second[0] > 1:
                self.requests_this_second.popleft()
            
            if len(self.requests_this_second) >= self.max_requests_per_second:
                # Wait until the oldest request in this second expires
                oldest_this_second = self.requests_this_second[0]
                wait_time = 1.0 - (now - oldest_this_second)
                return max(0.1, wait_time)
            
            # Check per-minute limit
            if not self.request_times:
                return 0.0
            
            oldest_request = self.request_times[0]
            effective_limit = int(self.max_requests_per_minute * self.throttle_factor)
            
            if len(self.request_times) >= effective_limit:
                wait_time = 60 - (now - oldest_request)
                return max(0.1, wait_time)
            
            return 0.0
    
    def acquire(self):
        """Acquire permission to make a request with circuit breaker protection"""
        # Check circuit breaker first
        if self.is_circuit_open():
            wait_time = self.recovery_timeout - (time.time() - self.last_failure_time)
            if wait_time > 0:
                logger.info(f"Gemini circuit breaker OPEN - waiting {wait_time:.1f}s for recovery")
                time.sleep(wait_time)
            if self.is_circuit_open():
                raise Exception("Gemini circuit breaker is OPEN - API unavailable")
        
        # Apply backoff delay
        if self.failure_count > 0:
            backoff_delay = self.get_backoff_delay()
            if backoff_delay > 0.1:
                time.sleep(backoff_delay)
        
        # Wait for concurrent request slot
        self.semaphore.acquire()
        
        # Wait for rate limit slot
        wait_time = self.wait_for_slot()
        if wait_time > 0:
            logger.debug(f"Gemini rate limit: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        with self.lock:
            now = time.time()
            self.request_times.append(now)
            self.requests_this_second.append(now)
            self.concurrent_requests += 1
    
    def release(self, success: bool = True):
        """Release request slot and update success metrics"""
        if success:
            self.record_success()
        else:
            self.record_failure()
        
        with self.lock:
            self.concurrent_requests -= 1
            
            # Update adaptive throttling - more conservative for Gemini
            if self.adaptive_rate_limiting:
                now = time.time()
                
                if not success:
                    self.recent_errors.append(now)
                
                # Remove old errors
                while self.recent_errors and now - self.recent_errors[0] > 300:
                    self.recent_errors.popleft()
                
                # Calculate error rate and adjust throttle more aggressively
                total_recent = len([t for t in self.request_times if now - t < 300])
                if total_recent > 5:  # Adjust with less data for Gemini
                    error_rate = len(self.recent_errors) / total_recent
                    
                    if error_rate > 0.1:  # More than 10% errors - be very aggressive
                        self.throttle_factor = max(0.2, self.throttle_factor * 0.6)
                    elif error_rate > 0.05:  # More than 5% errors
                        self.throttle_factor = max(0.4, self.throttle_factor * 0.8)
                    elif error_rate < 0.01:  # Less than 1% errors - slowly increase
                        self.throttle_factor = min(0.8, self.throttle_factor * 1.01)  # Cap at 80%
        
        self.semaphore.release()
    
    def get_optimal_batch_size(self) -> int:
        """Get optimal batch size - very conservative for Gemini"""
        if self.circuit_state == "OPEN":
            return 1
        elif self.throttle_factor < 0.5:
            return 1
        elif self.throttle_factor < 0.7:
            return 2
        else:
            return 3  # Never go above 3 for Gemini free tier
    
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        with self.lock:
            if self.circuit_state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.circuit_state = "HALF_OPEN"
                    self.half_open_calls = 0
                    logger.info("Gemini circuit breaker transitioning to HALF_OPEN state")
                    return False
                return True
            return False
    
    def record_success(self):
        """Record a successful API call"""
        with self.lock:
            if self.circuit_state == "HALF_OPEN":
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.circuit_state = "CLOSED"
                    self.failure_count = 0
                    self.current_delay = self.initial_delay
                    logger.info("Gemini circuit breaker CLOSED - API recovered")
            elif self.circuit_state == "CLOSED":
                if self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)
                    self.current_delay = max(self.initial_delay, self.current_delay / self.multiplier)
    
    def record_failure(self):
        """Record a failed API call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            self.current_delay = min(self.max_delay, self.current_delay * self.multiplier)
            
            if self.circuit_state == "HALF_OPEN":
                self.circuit_state = "OPEN"
                logger.warning("Gemini circuit breaker OPEN - API still failing")
            elif self.failure_count >= self.failure_threshold:
                self.circuit_state = "OPEN"
                logger.warning(f"Gemini circuit breaker OPEN - {self.failure_count} consecutive failures")
    
    def get_backoff_delay(self) -> float:
        """Get current backoff delay with jitter"""
        delay = self.current_delay
        if self.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0.1, delay)


class LlamaRateLimiter:
    """Advanced rate limiter for Llama API with circuit breaker and adaptive throttling"""
    
    def __init__(self, config: Config):
        self.config = config
        llama_perf = config.llama.get('performance', {})
        
        self.max_requests_per_minute = llama_perf.get('max_requests_per_minute', 2000)
        self.max_concurrent = llama_perf.get('max_concurrent_requests', 15)
        self.adaptive_rate_limiting = llama_perf.get('adaptive_rate_limiting', True)
        self.burst_mode = llama_perf.get('burst_mode', False)
        
        # Circuit breaker configuration
        cb_config = llama_perf.get('circuit_breaker', {})
        self.failure_threshold = cb_config.get('failure_threshold', 5)
        self.recovery_timeout = cb_config.get('recovery_timeout', 30)
        self.half_open_max_calls = cb_config.get('half_open_max_calls', 3)
        
        # Backoff strategy
        backoff_config = llama_perf.get('backoff_strategy', {})
        self.initial_delay = backoff_config.get('initial_delay', 1.0)
        self.max_delay = backoff_config.get('max_delay', 60.0)
        self.multiplier = backoff_config.get('multiplier', 2.0)
        self.jitter = backoff_config.get('jitter', True)
        
        # Rate limiting state
        self.request_times = deque()
        self.concurrent_requests = 0
        self.lock = threading.Lock()
        self.semaphore = threading.Semaphore(self.max_concurrent)
        
        # Adaptive throttling
        self.success_rate = 1.0
        self.recent_errors = deque()
        self.throttle_factor = 1.0
        self.current_delay = self.initial_delay
        
        # Circuit breaker state
        self.circuit_state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while self.request_times and now - self.request_times[0] > 60:
                self.request_times.popleft()
            
            # Apply adaptive throttling
            effective_limit = int(self.max_requests_per_minute * self.throttle_factor)
            
            return len(self.request_times) < effective_limit
    
    def wait_for_slot(self) -> float:
        """Calculate how long to wait for the next available slot"""
        with self.lock:
            if not self.request_times:
                return 0.0
            
            now = time.time()
            oldest_request = self.request_times[0]
            
            # If we're at the limit, wait until the oldest request is 1 minute old
            if len(self.request_times) >= int(self.max_requests_per_minute * self.throttle_factor):
                wait_time = 60 - (now - oldest_request)
                return max(0, wait_time)
            
            return 0.0
    
    def acquire(self):
        """Acquire permission to make a request with circuit breaker protection"""
        # Check circuit breaker first
        if self.is_circuit_open():
            # Circuit is open, wait for recovery timeout
            wait_time = self.recovery_timeout - (time.time() - self.last_failure_time)
            if wait_time > 0:
                logger.info(f"Circuit breaker OPEN - waiting {wait_time:.1f}s for recovery")
                time.sleep(wait_time)
            # Re-check after waiting
            if self.is_circuit_open():
                raise Exception("Circuit breaker is OPEN - API unavailable")
        
        # Apply minimal backoff delay only when necessary
        if self.failure_count > 2:
            backoff_delay = min(0.5, self.get_backoff_delay())
            if backoff_delay > 0.1:
                time.sleep(backoff_delay)
        
        # Wait for concurrent request slot
        self.semaphore.acquire()
        
        # Wait for rate limit slot
        wait_time = self.wait_for_slot()
        if wait_time > 0:
            time.sleep(wait_time)
        
        with self.lock:
            self.request_times.append(time.time())
            self.concurrent_requests += 1
    
    def release(self, success: bool = True):
        """Release request slot and update success metrics with circuit breaker"""
        # Update circuit breaker state
        if success:
            self.record_success()
        else:
            self.record_failure()
        
        with self.lock:
            self.concurrent_requests -= 1
            
            # Update adaptive throttling
            if self.adaptive_rate_limiting:
                now = time.time()
                
                # Track recent errors (last 5 minutes)
                if not success:
                    self.recent_errors.append(now)
                
                # Remove old errors
                while self.recent_errors and now - self.recent_errors[0] > 300:
                    self.recent_errors.popleft()
                
                # Calculate success rate and adjust throttle
                total_recent = len([t for t in self.request_times if now - t < 300])
                if total_recent > 10:  # Only adjust if we have enough data
                    error_rate = len(self.recent_errors) / total_recent
                    
                    if error_rate > 0.15:  # More than 15% errors - be more aggressive
                        self.throttle_factor = max(0.3, self.throttle_factor * 0.8)
                    elif error_rate > 0.05:  # More than 5% errors
                        self.throttle_factor = max(0.5, self.throttle_factor * 0.9)
                    elif error_rate < 0.02:  # Less than 2% errors
                        self.throttle_factor = min(1.0, self.throttle_factor * 1.02)
        
        self.semaphore.release()
    
    def get_optimal_batch_size(self) -> int:
        """Get optimal batch size based on current performance"""
        base_batch_size = self.config.llama.get('performance', {}).get('optimal_batch_size', 2)
        
        if self.adaptive_rate_limiting:
            # Reduce batch size if we're having errors or circuit is open
            if self.circuit_state == "OPEN":
                return 1
            elif self.throttle_factor < 0.8:
                return max(1, base_batch_size // 2)
            elif self.throttle_factor > 0.95 and self.circuit_state == "CLOSED":
                return min(4, base_batch_size * 2)
        
        return base_batch_size
    
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        with self.lock:
            if self.circuit_state == "OPEN":
                # Check if recovery timeout has passed
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.circuit_state = "HALF_OPEN"
                    self.half_open_calls = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN state")
                    return False
                return True
            return False
    
    def record_success(self):
        """Record a successful API call"""
        with self.lock:
            if self.circuit_state == "HALF_OPEN":
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.circuit_state = "CLOSED"
                    self.failure_count = 0
                    self.current_delay = self.initial_delay
                    logger.info("Circuit breaker CLOSED - API recovered")
            elif self.circuit_state == "CLOSED":
                # Reset failure count on success
                if self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)
                    self.current_delay = max(self.initial_delay, self.current_delay / self.multiplier)
    
    def record_failure(self):
        """Record a failed API call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Increase delay with exponential backoff
            self.current_delay = min(self.max_delay, self.current_delay * self.multiplier)
            
            if self.circuit_state == "HALF_OPEN":
                # Failure in half-open state, go back to open
                self.circuit_state = "OPEN"
                logger.warning("Circuit breaker OPEN - API still failing")
            elif self.failure_count >= self.failure_threshold:
                # Too many failures, open the circuit
                self.circuit_state = "OPEN"
                logger.warning(f"Circuit breaker OPEN - {self.failure_count} consecutive failures")
    
    def get_backoff_delay(self) -> float:
        """Get current backoff delay with optional jitter"""
        delay = self.current_delay
        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0.1, delay)

def quick_quality_filter(image_path: str, config) -> bool:
    """Fast pre-filtering based on file properties"""
    try:
        # Check file size
        file_size = os.path.getsize(image_path)
        min_size_kb = getattr(config, 'min_file_size_kb', 100) * 1024
        if file_size < min_size_kb:
            return False
        
        # Check image dimensions
        with Image.open(image_path) as img:
            width, height = img.size
            min_resolution = getattr(config, 'min_resolution', [800, 600])
            min_width = min_resolution[0] if len(min_resolution) > 0 else 800
            min_height = min_resolution[1] if len(min_resolution) > 1 else 600
            
            if width < min_width or height < min_height:
                return False
                
        return True
    except Exception:
        return False

def setup_cli_args():
    """Setup command line arguments"""
    parser = argparse.ArgumentParser(description="Instagram Photo Organizer with AI Analysis")
    
    # Basic options
    parser.add_argument("--source", "-s", help="Source folder path")
    parser.add_argument("--output", "-o", help="Output folder path")
    parser.add_argument("--config", "-c", default="config.json", help="Config file path")
    
    # Processing options
    parser.add_argument("--dev-mode", "-d", action="store_true", help="Enable development mode")
    parser.add_argument("--limit", "-l", type=int, help="Limit photos in dev mode")
    parser.add_argument("--post-size", "-p", type=int, help="Photos per post")
    parser.add_argument("--similarity", type=int, help="Similarity threshold (0-10)")
    
    # AI Provider options
    parser.add_argument("--ai-provider", choices=['llama', 'ollama', 'gemini'], help="AI provider to use")
    parser.add_argument("--llama-key", help="Llama API key")
    parser.add_argument("--gemini-key", help="Gemini API key")
    parser.add_argument("--ollama-url", help="Ollama API URL")
    parser.add_argument("--ollama-model", help="Ollama model name")
    
    # Mode selection
    parser.add_argument("--simple-mode", action="store_true", help="Run in simple mode (core features only)")
    
    # Performance options
    parser.add_argument("--parallel-workers", type=int, help="Number of parallel AI analysis workers")
    parser.add_argument("--batch-size", type=int, help="Batch size for AI analysis")
    parser.add_argument("--fast-mode", action="store_true", help="Enable fast processing mode")
    parser.add_argument("--no-cache", action="store_true", help="Disable AI analysis caching")
    
    # Contextual filtering options
    parser.add_argument("--no-contextual-filter", action="store_true", help="Disable AI-based contextual similarity filtering")
    parser.add_argument("--contextual-threshold", type=float, help="Contextual similarity threshold (0.0-1.0)")
    
    return parser.parse_args()

def get_exif_datetime(image_path: str) -> datetime.datetime:
    """Extract creation datetime from image EXIF data"""
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                        try:
                            return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            continue
    except Exception as e:
        logger.debug(f"Could not read EXIF data from {image_path}: {e}")
    
    return datetime.datetime.fromtimestamp(os.path.getmtime(image_path))

def fast_prefilter_images(image_paths: List[str], config: Config) -> List[str]:
    """Quick pre-filter based on file size and basic properties"""
    if not config.enable_prefilter or len(image_paths) < 100:
        return image_paths
    
    logger.info("Pre-filtering images by file size and metadata...")
    
    size_groups = defaultdict(list)
    
    # Create progress bar if tqdm is available
    if TQDM_AVAILABLE:
        iterator = tqdm(image_paths, desc="Pre-filtering by size", unit="img")
    else:
        iterator = image_paths
        logger.info("Processing file sizes...")
    
    processed_count = 0
    for path in iterator:
        try:
            size = os.path.getsize(path)
            # Group by approximate size (within 10% tolerance for pre-filter)
            size_key = size // max(1, int(size * 0.1))
            size_groups[size_key].append(path)
            
            if TQDM_AVAILABLE:
                iterator.set_postfix({"Size": f"{size//1024}KB", "Groups": len(size_groups)})
            
            processed_count += 1
            if not TQDM_AVAILABLE and processed_count % 100 == 0:
                logger.info(f"Processed {processed_count}/{len(image_paths)} files...")
                
        except Exception as e:
            logger.debug(f"Could not get size for {path}: {e}")
            # Add to a default group for files we can't read
            size_groups[0].append(path)
    
    # Count groups that need hash comparison
    groups_needing_hash = sum(1 for group in size_groups.values() if len(group) > 1)
    total_in_groups = sum(len(group) for group in size_groups.values() if len(group) > 1)
    
    logger.info(f"Pre-filter results:")
    logger.info(f"  - {len(size_groups)} size groups created")
    logger.info(f"  - {groups_needing_hash} groups need hash comparison")
    logger.info(f"  - {total_in_groups} images need detailed analysis")
    logger.info(f"  - {len(image_paths) - total_in_groups} images are unique by size")
    
    return image_paths

def compute_image_hash(path_and_config: tuple) -> tuple:
    """Compute hash for a single image - designed for parallel processing"""
    path, thumbnail_size, hash_size = path_and_config
    try:
        with Image.open(path) as img:
            # Resize image for faster hashing
            img.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
            img_hash = imagehash.phash(img, hash_size=hash_size)
            return path, img_hash, True, None
    except Exception as e:
        return path, None, False, str(e)

def filter_contextually_similar_images(analyzed_data: List[Dict], config: Config) -> List[Dict]:
    """Filter images with similar context using AI analysis"""
    if not config.enable_contextual_filtering:
        return analyzed_data
    
    logger.info(f"Filtering {len(analyzed_data)} images for contextual similarity")
    
    # Group images by similar context
    context_groups = []
    processed_indices = set()
    
    for i, photo1 in enumerate(analyzed_data):
        if i in processed_indices:
            continue
            
        # Start a new context group
        current_group = [photo1]
        processed_indices.add(i)
        
        # Find similar context photos
        for j, photo2 in enumerate(analyzed_data[i+1:], i+1):
            if j in processed_indices:
                continue
                
            similarity_score = calculate_contextual_similarity(photo1, photo2)
            
            if similarity_score >= config.contextual_similarity_threshold:
                current_group.append(photo2)
                processed_indices.add(j)
        
        context_groups.append(current_group)
    
    # Select best photo from each context group
    filtered_photos = []
    skipped_count = 0
    
    for group in context_groups:
        if len(group) == 1:
            filtered_photos.append(group[0])
        else:
            # Select best photo from the group
            best_photo = select_best_from_context_group(group, config)
            filtered_photos.append(best_photo)
            skipped_count += len(group) - 1
            
            # Get category from enhanced or analysis data
            category = best_photo.get('enhanced', {}).get('category') or best_photo['analysis'].get('category', 'unknown')
            logger.debug(f"Context group: kept 1/{len(group)} photos - {category} scene")
    
    logger.info(f"Contextual filtering: kept {len(filtered_photos)} photos, skipped {skipped_count} contextually similar")
    return filtered_photos

def calculate_contextual_similarity(photo1: Dict, photo2: Dict) -> float:
    """Calculate contextual similarity between two photos based on AI analysis"""
    analysis1 = photo1.get('analysis', {})
    analysis2 = photo2.get('analysis', {})
    
    # Category similarity (40% weight)
    category_score = 1.0 if analysis1.get('category') == analysis2.get('category') else 0.0
    subcategory_score = 1.0 if analysis1.get('subcategory') == analysis2.get('subcategory') else 0.0
    
    # Location/setting similarity (30% weight)
    location1 = (analysis1.get('location') or '').lower()
    location2 = (analysis2.get('location') or '').lower()
    location_score = calculate_text_similarity(location1, location2)
    
    # Mood similarity (20% weight)
    mood_score = 1.0 if analysis1.get('mood') == analysis2.get('mood') else 0.0
    
    # People count similarity (10% weight)
    people1 = analysis1.get('people_present', '0')
    people2 = analysis2.get('people_present', '0')
    people_score = 1.0 if people1 == people2 else 0.0
    
    # Weighted similarity score
    similarity = (
        category_score * 0.25 +
        subcategory_score * 0.15 +
        location_score * 0.30 +
        mood_score * 0.20 +
        people_score * 0.10
    )
    
    return similarity

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text descriptions"""
    if not text1 or not text2:
        return 0.0
    
    # Simple word overlap similarity
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def select_best_from_context_group(group: List[Dict], config: Config) -> Dict:
    """Select the best photo from a group of contextually similar photos"""
    
    # Helper function to get composite score from either enhanced or analysis data
    def get_composite_score(photo):
        if 'enhanced' in photo and 'composite_score' in photo['enhanced']:
            return photo['enhanced']['composite_score']
        return photo['analysis'].get('composite_score', 0)
    
    # Strategy 1: Highest composite score (default)
    if config.contextual_selection_strategy == 'highest_score':
        return max(group, key=get_composite_score)
    
    # Strategy 2: Most unique (lowest similarity to others)
    elif config.contextual_selection_strategy == 'most_unique':
        best_photo = None
        lowest_avg_similarity = float('inf')
        
        for candidate in group:
            similarities = []
            for other in group:
                if candidate != other:
                    sim = calculate_contextual_similarity(candidate, other)
                    similarities.append(sim)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0
            if avg_similarity < lowest_avg_similarity:
                lowest_avg_similarity = avg_similarity
                best_photo = candidate
        
        return best_photo or group[0]
    
    # Strategy 3: Best technical quality
    elif config.contextual_selection_strategy == 'best_technical':
        return max(group, key=lambda p: p['analysis'].get('technical_score', 0))
    
    # Strategy 4: Highest engagement potential
    elif config.contextual_selection_strategy == 'best_engagement':
        return max(group, key=lambda p: p['analysis'].get('engagement_score', 0))
    
    # Default fallback
    return max(group, key=get_composite_score)

def filter_similar_images(image_paths: List[str], threshold: int = 5, config: Config = None) -> List[str]:
    """Find and remove visually similar images using optimized perceptual hashing"""
    
    # Use config settings or defaults
    if config:
        parallel_workers = config.parallel_workers
        thumbnail_size = config.thumbnail_size
        hash_size = config.hash_size
        enable_prefilter = config.enable_prefilter
    else:
        parallel_workers = 4
        thumbnail_size = 256
        hash_size = 8
        enable_prefilter = True
    
    logger.info(f"Filtering {len(image_paths)} images for similarity (threshold: {threshold})")
    logger.info(f"Using {parallel_workers} workers, {thumbnail_size}px thumbnails, hash_size={hash_size}")
    
    # Step 0: Optional pre-filtering
    if enable_prefilter and len(image_paths) > 200:
        image_paths = fast_prefilter_images(image_paths, config)
    
    # Step 1: Generate hashes with progress tracking and parallel processing
    logger.info("Computing image hashes...")
    hashes = {}
    failed_paths = []
    
    # Prepare arguments for parallel processing
    hash_args = [(path, thumbnail_size, hash_size) for path in image_paths]
    
    # Use ThreadPoolExecutor for I/O bound operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        # Submit all tasks
        future_to_path = {executor.submit(compute_image_hash, args): args[0] for args in hash_args}
        
        # Process results with progress bar
        if TQDM_AVAILABLE:
            progress_bar = tqdm(total=len(image_paths), desc="Computing hashes", unit="img")
        else:
            progress_bar = None
            logger.info(f"Computing hashes for {len(image_paths)} images...")
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_path):
            path, img_hash, success, error = future.result()
            completed += 1
            
            if success and img_hash is not None:
                hashes[path] = img_hash
                if progress_bar:
                    progress_bar.set_postfix({
                        "Success": len(hashes),
                        "Failed": len(failed_paths),
                        "Current": os.path.basename(path)[:15]
                    })
                elif completed % 50 == 0:
                    logger.info(f"Processed {completed}/{len(image_paths)} images...")
            else:
                failed_paths.append(path)
                logger.debug(f"Failed to hash {os.path.basename(path)}: {error}")
                if progress_bar:
                    progress_bar.set_postfix({
                        "Success": len(hashes),
                        "Failed": len(failed_paths),
                        "Error": os.path.basename(path)[:15]
                    })
            
            if progress_bar:
                progress_bar.update(1)
        
        if progress_bar:
            progress_bar.close()
    
    logger.info(f"Hash computation complete: {len(hashes)} successful, {len(failed_paths)} failed")
    
    # Step 2: Group similar images using optimized comparison
    logger.info("Finding similar image groups...")
    
    # Convert to list for indexed access
    hash_items = list(hashes.items())
    unique_paths = []
    processed = set()
    skipped_count = 0
    similar_groups_found = 0
    
    if TQDM_AVAILABLE:
        progress_bar = tqdm(total=len(hash_items), desc="Finding duplicates", unit="img")
    else:
        progress_bar = None
        logger.info(f"Comparing {len(hash_items)} image hashes...")
    
    for i, (path1, hash1) in enumerate(hash_items):
        if path1 in processed:
            if progress_bar:
                progress_bar.update(1)
            continue
        
        # This image is unique so far
        unique_paths.append(path1)
        processed.add(path1)
        
        # Find all similar images to this one
        similar_group = [path1]
        
        # Only compare with remaining images (optimization)
        for j in range(i + 1, len(hash_items)):
            path2, hash2 = hash_items[j]
            
            if path2 in processed:
                continue
            
            # Check similarity
            hash_diff = abs(hash1 - hash2)
            if hash_diff <= threshold:
                similar_group.append(path2)
                processed.add(path2)
                skipped_count += 1
        
        # Log similar groups
        if len(similar_group) > 1:
            similar_groups_found += 1
            group_names = [os.path.basename(p) for p in similar_group[:3]]
            if len(similar_group) > 3:
                group_names.append(f"...+{len(similar_group)-3} more")
            logger.info(f"Similar group #{similar_groups_found} ({len(similar_group)} images): {', '.join(group_names)}")
        
        if progress_bar:
            progress_bar.set_postfix({
                "Unique": len(unique_paths), 
                "Skipped": skipped_count,
                "Groups": similar_groups_found,
                "Current": os.path.basename(path1)[:15]
            })
            progress_bar.update(1)
        elif i % 50 == 0:
            logger.info(f"Processed {i}/{len(hash_items)} comparisons...")
    
    if progress_bar:
        progress_bar.close()
    
    # Include failed images (they couldn't be processed for similarity)
    unique_paths.extend(failed_paths)
    
    # Final summary
    logger.info("=" * 50)
    logger.info("SIMILARITY FILTERING COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Original images: {len(image_paths)}")
    logger.info(f"Successfully processed: {len(hashes)}")
    logger.info(f"Failed to process: {len(failed_paths)}")
    logger.info(f"Similar groups found: {similar_groups_found}")
    logger.info(f"Similar images skipped: {skipped_count}")
    logger.info(f"Unique images kept: {len(unique_paths)}")
    logger.info(f"Space saved: {skipped_count} duplicate images removed")
    logger.info("=" * 50)
    
    return unique_paths

def convert_and_prepare_images(source_dir: str, temp_dir: str, all_source_paths: List[str], quality: int = 95) -> Tuple[str, List[str]]:
    """Convert HEIC images to JPG and prepare final image paths (optimized - no unnecessary conversions)"""
    logger.info("Preparing images and converting HEIC files...")
    
    # Create unique temp directory based on source folder to avoid conflicts
    import hashlib
    source_hash = hashlib.md5(source_dir.encode()).hexdigest()[:8]
    unique_temp_dir = f"{temp_dir}_{source_hash}"
    
    # Clean and recreate temp directory to ensure no old files
    if os.path.exists(unique_temp_dir):
        import shutil
        logger.info(f"Cleaning existing temp directory: {unique_temp_dir}")
        shutil.rmtree(unique_temp_dir)
    
    Path(unique_temp_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using temp directory: {unique_temp_dir}")
    
    converted_count = 0
    used_original_count = 0
    error_count = 0
    final_image_paths = []
    
    # Separate HEIC files from others
    heic_files = []
    ready_files = []
    
    for original_path in all_source_paths:
        filename = os.path.basename(original_path)
        base_name, extension = os.path.splitext(filename)
        
        if extension.lower() in ['.heic', '.heif']:
            heic_files.append(original_path)
        else:
            # JPG, JPEG, PNG files can be used directly
            ready_files.append(original_path)
    
    logger.info(f"Found {len(heic_files)} HEIC/HEIF files to convert, {len(ready_files)} files ready to use")
    
    # Add ready files directly to final paths (no conversion needed)
    final_image_paths.extend(ready_files)
    used_original_count = len(ready_files)
    
    # Only convert HEIC/HEIF files
    if heic_files:
        if TQDM_AVAILABLE:
            progress_bar = tqdm(heic_files, desc="Converting HEIC files", unit="img")
        else:
            progress_bar = heic_files
            logger.info(f"Converting {len(heic_files)} HEIC/HEIF files...")
        
        for i, original_path in enumerate(progress_bar if TQDM_AVAILABLE else heic_files):
            filename = os.path.basename(original_path)
            base_name, extension = os.path.splitext(filename)
            target_filename = base_name + ".jpg"
            destination_path = os.path.join(unique_temp_dir, target_filename)
            
            try:
                with Image.open(original_path) as image:
                    rgb_image = image.convert("RGB")
                    rgb_image.save(destination_path, "JPEG", quality=quality)
                    final_image_paths.append(destination_path)
                    converted_count += 1
                    
            except Exception as e:
                logger.error(f"Could not convert {filename}: {e}")
                error_count += 1
            
            if TQDM_AVAILABLE:
                progress_bar.set_postfix({
                    "Converted": converted_count,
                    "Errors": error_count
                })
            elif not TQDM_AVAILABLE and (i + 1) % 10 == 0:
                logger.info(f"Converted {i + 1}/{len(heic_files)} HEIC files...")
        
        if TQDM_AVAILABLE:
            progress_bar.close()
    
    logger.info(f"Image preparation complete:")
    logger.info(f"  - Used original files (JPG/PNG): {used_original_count}")
    logger.info(f"  - Converted (HEIC→JPG): {converted_count}")
    logger.info(f"  - Errors: {error_count}")
    logger.info(f"  - Total ready images: {len(final_image_paths)}")
    
    return unique_temp_dir, final_image_paths

def cleanup_temp_directory(temp_dir: str, keep_files: bool = False) -> None:
    """Clean up temporary directory after processing"""
    if not keep_files and os.path.exists(temp_dir):
        import shutil
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up temp directory {temp_dir}: {e}")
    elif keep_files:
        logger.info(f"Keeping temporary files in: {temp_dir}")

def encode_image_to_base64(image_path: str, config: Config = None) -> Optional[str]:
    """Encode image to base64 string with optimized settings"""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Use faster thumbnail size if config available
            if config and hasattr(config, 'enable_fast_mode') and config.enable_fast_mode:
                thumbnail_size = (config.fast_thumbnail_size, config.fast_thumbnail_size)
                quality = config.fast_jpeg_quality
            else:
                thumbnail_size = THUMBNAIL_SIZE
                quality = 85
            
            img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=quality)
            
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
            
    except Exception as e:
        logger.error(f"Could not encode image {image_path}: {e}")
        return None

def analyze_image_with_ai(image_path: str, config: Config) -> Optional[Dict]:
    """Analyze image using configured AI provider with caching"""
    
    # Check cache first if enabled
    if config.enable_caching:
        cache_key = get_image_hash_for_cache(image_path)
        with _cache_lock:
            if cache_key in _analysis_cache:
                cache_entry = _analysis_cache[cache_key]
                # Check if cache is still valid
                cache_age_hours = (time.time() - cache_entry['timestamp']) / 3600
                if cache_age_hours < config.cache_duration_hours:
                    logger.debug(f"Using cached analysis for {os.path.basename(image_path)}")
                    return cache_entry['result']
                else:
                    # Remove expired cache entry
                    del _analysis_cache[cache_key]
    
    logger.info(f"Analyzing: {os.path.basename(image_path)} using {config.ai_provider}")
    
    base64_image = encode_image_to_base64(image_path, config)
    if not base64_image:
        return None
    
    # Analyze with retries
    result = None
    for attempt in range(config.ai_max_retries):
        try:
            if config.ai_provider == 'gemini':
                result = analyze_with_gemini(base64_image, config)
            elif config.ai_provider == 'llama':
                result = analyze_with_llama(base64_image, config)
            else:
                result = analyze_with_ollama(base64_image, config)
            
            if result:
                break
                
        except Exception as e:
            logger.warning(f"Analysis attempt {attempt + 1} failed for {os.path.basename(image_path)}: {e}")
            if attempt < config.ai_max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
    
    # Cache the result if successful and caching is enabled
    if result and config.enable_caching:
        cache_key = get_image_hash_for_cache(image_path)
        with _cache_lock:
            _analysis_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
    
    return result

def analyze_images_parallel(image_paths: List[str], config: Config) -> List[Dict]:
    """Analyze multiple images in parallel with progress tracking and provider-specific optimizations"""
    logger.info(f"Starting parallel AI analysis of {len(image_paths)} images using {config.ai_parallel_workers} workers")
    
    # Pre-filter images for quality if fast mode is enabled
    if config.enable_fast_mode:
        logger.info("Pre-filtering images for quality...")
        filtered_paths = []
        for path in image_paths:
            if quick_quality_filter(path, config):
                filtered_paths.append(path)
        
        logger.info(f"Pre-filter: {len(filtered_paths)}/{len(image_paths)} images passed quality check")
        image_paths = filtered_paths
    
    # Use multi-provider processing for maximum speed
    if config.ai_provider == 'multi':
        logger.info("Using multi-provider processing for maximum speed")
        return analyze_images_multi_provider(image_paths, config)
    
    # Use optimized processing for Llama API
    elif config.ai_provider == 'llama' and len(image_paths) > 5:
        logger.info("Using optimized Llama batch processing")
        return analyze_images_llama_optimized(image_paths, config)
    
    # Use Gemini batch processing if available
    elif config.ai_provider == 'gemini' and len(image_paths) > 8:
        logger.info("Using optimized Gemini batch processing")
        return analyze_images_gemini_optimized(image_paths, config)
    
    # Default parallel processing for other providers or small batches
    results = []
    successful_analyses = 0
    
    with ThreadPoolExecutor(max_workers=config.ai_parallel_workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(analyze_image_with_ai, path, config): path 
            for path in image_paths
        }
        
        # Process completed tasks with progress tracking
        if TQDM_AVAILABLE:
            progress_bar = tqdm(
                as_completed(future_to_path), 
                total=len(future_to_path),
                desc="AI Analysis",
                unit="img"
            )
        else:
            progress_bar = as_completed(future_to_path)
        
        for future in progress_bar:
            path = future_to_path[future]
            try:
                result = future.result()
                if result:
                    results.append({
                        'path': path,
                        'analysis': result,
                        'datetime': get_exif_datetime(path)
                    })
                    successful_analyses += 1
                    
                    if TQDM_AVAILABLE:
                        progress_bar.set_postfix({
                            'Success': successful_analyses,
                            'Instagram-worthy': sum(1 for r in results if r['analysis'].get('instagram_worthy', False)),
                            'Quality': f"{sum(r['analysis'].get('composite_score', 0) for r in results) / len(results):.1f}/10" if results else "0/10"
                        })
                        
            except Exception as e:
                logger.error(f"Failed to analyze {os.path.basename(path)}: {e}")
    
    logger.info(f"Successfully analyzed {successful_analyses}/{len(image_paths)} images")
    return results

def analyze_images_multi_provider(image_paths: List[str], config: Config) -> List[Dict]:
    """Multi-provider analysis with load balancing and failover"""
    if config.ai_provider == "multi":
        return analyze_images_with_load_balancing(image_paths, config)
    elif config.ai_provider == "llama":
        return analyze_images_llama_optimized(image_paths, config)
    elif config.ai_provider == "gemini":
        return analyze_images_gemini_optimized(image_paths, config)
    else:
        return analyze_images_llama_optimized(image_paths, config)

def analyze_images_with_load_balancing(image_paths: List[str], config: Config) -> List[Dict]:
    """Load balance across multiple AI providers for maximum speed"""
    multi_config = config.config.get('multi_provider', {})
    providers = multi_config.get('providers', ['llama', 'gemini'])
    
    logger.info(f"Multi-provider processing: {len(image_paths)} images across {len(providers)} providers")
    
    # Split images across providers
    chunks = []
    chunk_size = len(image_paths) // len(providers)
    
    for i, provider in enumerate(providers):
        start_idx = i * chunk_size
        if i == len(providers) - 1:  # Last provider gets remaining images
            end_idx = len(image_paths)
        else:
            end_idx = start_idx + chunk_size
        
        if start_idx < len(image_paths):
            chunks.append((provider, image_paths[start_idx:end_idx]))
    
    results = []
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=len(providers)) as executor:
        futures = []
        
        for provider, chunk_paths in chunks:
            if provider == "llama":
                future = executor.submit(analyze_images_llama_optimized, chunk_paths, config)
            elif provider == "gemini":
                future = executor.submit(analyze_images_gemini_optimized, chunk_paths, config)
            else:
                future = executor.submit(analyze_images_llama_optimized, chunk_paths, config)
            
            futures.append((provider, future))
        
        # Collect results
        for provider, future in futures:
            try:
                chunk_results = future.result(timeout=300)  # 5 minute timeout per provider
                results.extend(chunk_results)
                logger.info(f"{provider} provider completed: {len(chunk_results)} images")
            except Exception as e:
                logger.error(f"{provider} provider failed: {e}")
    
    logger.info(f"Multi-provider analysis complete: {len(results)} total images processed")
    return results

def analyze_images_gemini_optimized(image_paths: List[str], config: Config) -> List[Dict]:
    """Optimized Gemini analysis with conservative rate limiting and circuit breaker"""
    logger.info(f"Gemini processing: {len(image_paths)} images with conservative rate limiting")
    
    # Initialize Gemini rate limiter
    rate_limiter = GeminiRateLimiter(config)
    results = []
    
    # Use much lower concurrency for Gemini free tier
    max_workers = 3  # Conservative for Gemini's 30 req/sec limit
    
    if TQDM_AVAILABLE:
        progress_bar = tqdm(total=len(image_paths), desc="Gemini Analysis", unit="img")
    
    # Process in smaller batches with intelligent sizing
    batch_size = rate_limiter.get_optimal_batch_size()
    batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
    
    logger.info(f"Processing {len(batches)} batches of size {batch_size} with {max_workers} workers")
    
    for batch_idx, batch in enumerate(batches):
        logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} images)")
        
        batch_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for path in batch:
                future = executor.submit(analyze_single_image_gemini_with_limiter, path, config, rate_limiter)
                futures.append((future, path))
            
            for future, path in futures:
                try:
                    result = future.result(timeout=120)  # Longer timeout for rate-limited requests
                    if result:
                        batch_results.append(result)
                        results.append(result)
                    
                    if TQDM_AVAILABLE:
                        progress_bar.update(1)
                        progress_bar.set_postfix({
                            'Success': len(results),
                            'Batch': f"{batch_idx + 1}/{len(batches)}",
                            'Throttle': f"{rate_limiter.throttle_factor:.2f}",
                            'Circuit': rate_limiter.circuit_state
                        })
                except Exception as e:
                    logger.error(f"Gemini analysis failed for {os.path.basename(path)}: {e}")
                    if TQDM_AVAILABLE:
                        progress_bar.update(1)
        
        # Adaptive delay between batches based on performance
        if batch_idx < len(batches) - 1:  # Don't delay after last batch
            if rate_limiter.circuit_state == "OPEN":
                delay = 10.0  # Long delay if circuit is open
            elif rate_limiter.throttle_factor < 0.5:
                delay = 5.0   # Medium delay if heavily throttled
            elif len(batch_results) < len(batch) * 0.8:  # Less than 80% success
                delay = 3.0   # Short delay if some failures
            else:
                delay = 1.0   # Minimal delay if all good
            
            logger.debug(f"Inter-batch delay: {delay}s (throttle: {rate_limiter.throttle_factor:.2f})")
            time.sleep(delay)
        
        # Adjust batch size for next iteration
        new_batch_size = rate_limiter.get_optimal_batch_size()
        if new_batch_size != batch_size:
            batch_size = new_batch_size
            logger.info(f"Adjusted batch size to {batch_size} based on performance")
    
    if TQDM_AVAILABLE:
        progress_bar.close()
    
    logger.info(f"Gemini processing complete: {len(results)}/{len(image_paths)} images analyzed successfully")
    return results


def analyze_single_image_gemini_with_limiter(image_path: str, config: Config, rate_limiter: GeminiRateLimiter) -> Optional[Dict]:
    """Analyze single image with Gemini API using rate limiter"""
    try:
        # Acquire rate limit permission
        rate_limiter.acquire()
        
        # Perform the actual analysis
        result = analyze_single_image_gemini_direct(image_path, config)
        
        # Record success/failure
        rate_limiter.release(success=result is not None)
        
        return result
        
    except Exception as e:
        # Record failure
        rate_limiter.release(success=False)
        logger.error(f"Rate-limited Gemini analysis failed for {os.path.basename(image_path)}: {e}")
        return None


def analyze_single_image_gemini_direct(image_path: str, config: Config) -> Optional[Dict]:
    """Direct Gemini analysis without rate limiting (used internally)"""

def analyze_single_image_gemini_direct(image_path: str, config: Config) -> Optional[Dict]:
    """Analyze single image with Gemini API (direct call without rate limiting)"""
    try:
        # Convert image to base64
        with open(image_path, "rb") as img:
            base64_image = base64.b64encode(img.read()).decode('utf-8')
        
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
        
        url = f"{config.gemini['api_url']}/{config.gemini['model']}:generateContent"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
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
                "maxOutputTokens": 1024,
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": config.gemini["api_key"]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            analysis = json.loads(content)
            
            # Calculate composite score
            weights = {
                'technical_score': 0.15,
                'visual_appeal': 0.25,
                'engagement_score': 0.30,
                'uniqueness': 0.20,
                'story_potential': 0.10
            }
            
            composite_score = sum(
                analysis.get(field, 5.0) * weight 
                for field, weight in weights.items()
            )
            
            analysis['composite_score'] = round(composite_score, 2)
            
            # Determine tier
            if composite_score >= 8.5:
                tier = "premium"
            elif composite_score >= 7.5:
                tier = "excellent"
            elif composite_score >= 6.0:
                tier = "good"
            elif composite_score >= 4.0:
                tier = "average"
            else:
                tier = "poor"
            
            analysis['instagram_tier'] = tier
            analysis['instagram_worthy'] = tier in ['premium', 'excellent'] or composite_score >= 7.0
            
            return {
                'image_path': image_path,
                'analysis': analysis,
                'provider': 'gemini'
            }
    
    except Exception as e:
        logger.error(f"Gemini analysis failed for {os.path.basename(image_path)}: {e}")
        return None

def analyze_images_llama_optimized(image_paths: List[str], config: Config) -> List[Dict]:
    """Optimized analysis for Llama API with adaptive batch processing and circuit breaker"""
    global _llama_rate_limiter
    
    if _llama_rate_limiter is None:
        _llama_rate_limiter = LlamaRateLimiter(config)
    
    # Start with aggressive settings for speed
    max_workers = min(config.ai_parallel_workers, 15)
    
    logger.info(f"Llama high-speed processing: {len(image_paths)} images, using {max_workers} workers")
    
    results = []
    successful_analyses = 0
    consecutive_failures = 0
    
    if TQDM_AVAILABLE:
        progress_bar = tqdm(total=len(image_paths), desc="Llama Analysis", unit="img")
    
    # Process images in adaptive batches
    i = 0
    while i < len(image_paths):
        # Adjust batch size based on current performance
        current_batch_size = _llama_rate_limiter.get_optimal_batch_size()
        
        # If circuit is open or many failures, process one at a time
        if _llama_rate_limiter.circuit_state == "OPEN" or consecutive_failures > 3:
            current_batch_size = 1
            max_workers = 1
        elif consecutive_failures > 0:
            current_batch_size = max(1, current_batch_size // 2)
            max_workers = min(max_workers, 2)
        
        # Get next batch
        batch_end = min(i + current_batch_size * max_workers, len(image_paths))
        batch_paths = image_paths[i:batch_end]
        
        logger.debug(f"Processing batch {i//current_batch_size + 1}: {len(batch_paths)} images, {max_workers} workers")
        
        batch_results = []
        batch_failures = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit batch with staggered timing to avoid overwhelming API
            futures = []
            for j, path in enumerate(batch_paths):
                # Add small delay between submissions to spread load
                if j > 0 and j % max_workers == 0:
                    time.sleep(0.5)
                
                future = executor.submit(analyze_single_image_llama, path, config)
                futures.append((future, path))
            
            # Collect results with timeout
            for future, path in futures:
                try:
                    result = future.result(timeout=120)  # Longer timeout for stability
                    if result:
                        batch_results.append(result)
                        successful_analyses += 1
                        consecutive_failures = 0  # Reset on success
                    else:
                        batch_failures += 1
                        consecutive_failures += 1
                        
                    if TQDM_AVAILABLE:
                        progress_bar.update(1)
                        progress_bar.set_postfix({
                            'Success': successful_analyses,
                            'Instagram-worthy': sum(1 for r in results if r['analysis'].get('instagram_worthy', False)),
                            'Quality': f"{sum(r['analysis'].get('composite_score', 0) for r in results) / len(results):.1f}/10" if results else "0/10",
                            'Rate': f"{_llama_rate_limiter.throttle_factor:.2f}x",
                            'Circuit': _llama_rate_limiter.circuit_state,
                            'Failures': consecutive_failures
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to analyze {os.path.basename(path)}: {e}")
                    batch_failures += 1
                    consecutive_failures += 1
                    if TQDM_AVAILABLE:
                        progress_bar.update(1)
        
        results.extend(batch_results)
        
        # Minimal delay only for high failure rates
        if batch_failures > 0:
            failure_rate = batch_failures / len(batch_paths)
            if failure_rate > 0.7:  # More than 70% failures
                time.sleep(1)  # Brief pause only
        
        i = batch_end
    
    if TQDM_AVAILABLE:
        progress_bar.close()
    
    logger.info(f"Llama adaptive analysis complete: {successful_analyses}/{len(image_paths)} successful")
    logger.info(f"Final throttle factor: {_llama_rate_limiter.throttle_factor:.2f}x")
    logger.info(f"Circuit breaker state: {_llama_rate_limiter.circuit_state}")
    
    return results

def analyze_single_image_llama(image_path: str, config: Config) -> Optional[Dict]:
    """Analyze single image with Llama API including rate limiting and caching"""
    # Check cache first
    if config.enable_caching:
        cache_key = get_image_hash_for_cache(image_path)
        with _cache_lock:
            if cache_key in _analysis_cache:
                cache_entry = _analysis_cache[cache_key]
                cache_age_hours = (time.time() - cache_entry['timestamp']) / 3600
                if cache_age_hours < config.cache_duration_hours:
                    return {
                        'path': image_path,
                        'analysis': cache_entry['result'],
                        'datetime': get_exif_datetime(image_path)
                    }
    
    # Encode image
    base64_image = encode_image_to_base64(image_path, config)
    if not base64_image:
        return None
    
    # Analyze with Llama
    result = analyze_with_llama(base64_image, config)
    if not result:
        return None
    
    # Cache result
    if config.enable_caching:
        cache_key = get_image_hash_for_cache(image_path)
        with _cache_lock:
            _analysis_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
    
    return {
        'path': image_path,
        'analysis': result,
        'datetime': get_exif_datetime(image_path)
    }

def make_rate_limited_request(url: str, payload: dict, headers: dict, config: Config, request_type: str = "batch") -> dict:
    """Make a rate-limited request with exponential backoff"""
    max_retries = config.ai_max_retries
    base_delay = 3.0 if request_type == "batch" else 1.0  # Longer delay for batch requests
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=config.ai_timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit error
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                    logger.warning(f"{request_type.title()} rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"{request_type.title()} rate limit exceeded after {max_retries + 1} attempts")
                    raise
            elif e.response.status_code == 503:  # Service unavailable
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(2, 5)  # Longer delay for 503
                    logger.warning(f"{request_type.title()} service unavailable (503), retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"{request_type.title()} service unavailable after {max_retries + 1} attempts")
                    raise
            else:
                logger.error(f"{request_type.title()} Gemini analysis error: {e}")
                raise
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"{request_type.title()} request failed, retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
                continue
            else:
                logger.error(f"{request_type.title()} request failed after {max_retries + 1} attempts: {e}")
                raise

def analyze_batch_with_gemini(image_paths: List[str], config: Config) -> List[Dict]:
    """Analyze multiple images in a single Gemini API request (up to 16 images)"""
    if len(image_paths) > 16:
        raise ValueError("Gemini batch analysis supports maximum 16 images per request")
    
    logger.info(f"Batch analyzing {len(image_paths)} images with Gemini")
    
    # Encode all images
    base64_images = []
    valid_paths = []
    
    for path in image_paths:
        encoded = encode_image_to_base64(path, config)
        if encoded:
            base64_images.append(encoded)
            valid_paths.append(path)
    
    if not base64_images:
        return []
    
    # Create batch prompt
    prompt_text = f"""Analyze these {len(base64_images)} images for Instagram and return a JSON array with {len(base64_images)} objects, each with these exact fields:

{{
  "technical_score": 7,
  "visual_appeal": 8,
  "engagement_score": 6,
  "uniqueness": 5,
  "story_potential": 7,
  "category": "portrait",
  "location": "outdoor setting with mountains",
  "mood": "peaceful"
}}

Rate technical_score, visual_appeal, engagement_score, uniqueness, and story_potential from 1-10.
Choose category from: landscape, portrait, food, architecture, lifestyle, travel, nature, street, action.
Return ONLY a JSON array with {len(base64_images)} objects, no markdown formatting."""

    url = f"{config.gemini['api_url']}/{config.gemini['model']}:generateContent"
    
    # Create parts array with text prompt and all images
    parts = [{"text": prompt_text}]
    for base64_image in base64_images:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64_image
            }
        })
    
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": config.gemini["api_key"]
    }
    
    try:
        response_data = make_rate_limited_request(url, payload, headers, config, "batch")
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            content = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            try:
                analyses = json.loads(content)
                if not isinstance(analyses, list):
                    analyses = [analyses]  # Handle single object response
                
                results = []
                for i, analysis in enumerate(analyses[:len(valid_paths)]):
                    # Fill in missing fields with defaults
                    required_fields = ['technical_score', 'visual_appeal', 'engagement_score', 'uniqueness']
                    for field in required_fields:
                        if field not in analysis:
                            analysis[field] = 5.0
                    
                    # Calculate composite score
                    weights = {
                        'technical_score': 0.15,
                        'visual_appeal': 0.25,
                        'engagement_score': 0.30,
                        'uniqueness': 0.20,
                        'story_potential': 0.10
                    }
                    
                    composite_score = (
                        analysis.get('technical_score', 5.0) * weights['technical_score'] +
                        analysis.get('visual_appeal', 5.0) * weights['visual_appeal'] +
                        analysis.get('engagement_score', 5.0) * weights['engagement_score'] +
                        analysis.get('uniqueness', 5.0) * weights['uniqueness'] +
                        analysis.get('story_potential', 5.0) * weights['story_potential']
                    )
                    analysis['composite_score'] = round(composite_score, 2)
                    
                    # Determine tier
                    if composite_score >= 8.5:
                        tier = "premium"
                    elif composite_score >= 7.5:
                        tier = "excellent"
                    elif composite_score >= 6.0:
                        tier = "good"
                    elif composite_score >= 4.0:
                        tier = "average"
                    else:
                        tier = "poor"
                    
                    analysis['instagram_tier'] = tier
                    analysis['instagram_worthy'] = tier in ['premium', 'excellent'] or composite_score >= 7.0
                    
                    results.append({
                        'path': valid_paths[i],
                        'analysis': analysis,
                        'datetime': get_exif_datetime(valid_paths[i])
                    })
                
                return results
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse batch Gemini JSON response: {e}")
                return []
        else:
            logger.warning("No candidates in batch Gemini response")
            return []
            
    except Exception as e:
        logger.error(f"Batch Gemini analysis error: {e}")
        
        # If it's a 503 error, fall back to individual analysis
        if "503" in str(e) or "Service Unavailable" in str(e):
            logger.warning("Gemini batch service unavailable, falling back to individual analysis")
            return analyze_images_individually_fallback(valid_paths, config)
        
        return []

def analyze_images_individually_fallback(image_paths: List[str], config: Config) -> List[Dict]:
    """Fallback to individual analysis when batch fails"""
    logger.info(f"Analyzing {len(image_paths)} images individually as fallback")
    
    results = []
    for i, path in enumerate(image_paths):
        logger.info(f"Analyzing image {i+1}/{len(image_paths)}: {os.path.basename(path)}")
        
        # Add delay between requests to avoid rate limiting
        if i > 0:
            time.sleep(config.rate_limit_delay)
        
        analysis = analyze_with_gemini(path, config)
        if analysis:
            results.append({
                'path': path,
                'analysis': analysis,
                'datetime': get_exif_datetime(path)
            })
    
    return results

def analyze_images_gemini_batched(image_paths: List[str], config: Config) -> List[Dict]:
    """Optimized Gemini analysis using existing batch processing"""
    results = []
    
    # Use existing Gemini batch processing (up to 16 images per batch)
    batch_size = 16
    
    if TQDM_AVAILABLE:
        progress_bar = tqdm(total=len(image_paths), desc="Gemini Batch", unit="img")
    
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i + batch_size]
        
        try:
            batch_results = analyze_batch_with_gemini(batch_paths, config)
            results.extend(batch_results)
            
            if TQDM_AVAILABLE:
                progress_bar.update(len(batch_paths))
                progress_bar.set_postfix({
                    'Batches': f"{(i//batch_size)+1}/{(len(image_paths)-1)//batch_size+1}",
                    'Success': len(results)
                })
                
        except Exception as e:
            logger.error(f"Gemini batch analysis failed: {e}")
            # Fallback to individual analysis for this batch
            for path in batch_paths:
                try:
                    base64_image = encode_image_to_base64(path, config)
                    if base64_image:
                        result = analyze_with_gemini(base64_image, config)
                        if result:
                            results.append({
                                'path': path,
                                'analysis': result,
                                'datetime': get_exif_datetime(path)
                            })
                except Exception as e2:
                    logger.error(f"Individual fallback failed for {os.path.basename(path)}: {e2}")
                
                if TQDM_AVAILABLE:
                    progress_bar.update(1)
    
    if TQDM_AVAILABLE:
        progress_bar.close()
    
    logger.info(f"Gemini batch analysis complete: {len(results)}/{len(image_paths)} successful")
    return results

def analyze_with_ollama(base64_image: str, config: Config) -> Optional[Dict]:
    """Analyze image using Ollama"""
    prompt_text = """Analyze this image for Instagram and return ONLY a JSON object with these exact fields:

{
  "technical_score": 7,
  "visual_appeal": 8,
  "engagement_score": 6,
  "uniqueness": 5,
  "story_potential": 7,
  "category": "portrait",
  "location": "outdoor setting with mountains",
  "mood": "peaceful",
  "strengths": ["good lighting", "nice composition"],
  "people_present": "1"
}

Rate technical_score, visual_appeal, engagement_score, uniqueness, and story_potential from 1-10.
Choose category from: landscape, portrait, food, architecture, lifestyle, travel, nature, street, action.
Return ONLY valid JSON, no markdown formatting."""
    
    payload = {
        "model": config.ollama["model"],
        "prompt": prompt_text,
        "images": [base64_image],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 4096}
    }
    
    try:
        response = requests.post(config.ollama["api_url"], json=payload, timeout=config.ollama["timeout"])
        response.raise_for_status()
        
        response_data = response.json()
        analysis = json.loads(response_data.get("response", "{}"))
        
        if "instagram_worthy" in analysis:
            return analysis
        else:
            logger.warning("Invalid Ollama analysis response")
            return None
            
    except Exception as e:
        logger.error(f"Ollama analysis error: {e}")
        return None

def analyze_with_llama(base64_image: str, config: Config) -> Optional[Dict]:
    """Analyze image using Llama API with advanced Instagram scoring and rate limiting"""
    global _llama_rate_limiter
    
    if not config.llama.get("api_key"):
        logger.error("Llama API key not provided. Set LLAMA_API_KEY environment variable or update config.")
        return None
    
    # Initialize rate limiter if needed
    if _llama_rate_limiter is None:
        _llama_rate_limiter = LlamaRateLimiter(config)
    
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
        "Authorization": f"Bearer {config.llama.get('api_key') or os.environ.get('LLAMA_API_KEY')}"
    }
    
    payload = {
        "model": config.llama["model"],
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
    
    # Use advanced rate limiting with circuit breaker
    try:
        _llama_rate_limiter.acquire()
    except Exception as e:
        logger.error(f"Rate limiter blocked request: {e}")
        return None
    
    try:
        # Use faster timeout for individual requests
        timeout = config.llama.get('performance', {}).get('fast_timeout', 30)
        
        # Add retry logic for 500 errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    config.llama["api_url"], 
                    headers=headers, 
                    json=payload, 
                    timeout=timeout
                )
                
                if response.status_code == 500 and attempt < max_retries - 1:
                    # Server error - wait and retry
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.warning(f"Llama API 500 error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                break
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Llama API request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        response_data = response.json()
        _llama_rate_limiter.release(success=True)
        
        # Debug: log the actual response structure
        logger.debug(f"Llama API response keys: {list(response_data.keys())}")
        logger.debug(f"Full Llama response: {response_data}")
        
        # Handle Llama API response format
        content = None
        if 'completion_message' in response_data and 'content' in response_data['completion_message']:
            # Llama API format: completion_message.content.text
            content_obj = response_data['completion_message']['content']
            if isinstance(content_obj, dict) and 'text' in content_obj:
                content = content_obj['text']
            elif isinstance(content_obj, str):
                content = content_obj
        elif 'choices' in response_data and len(response_data['choices']) > 0:
            # OpenAI format (fallback)
            content = response_data['choices'][0]['message']['content']
        else:
            logger.warning(f"Unexpected Llama response format. Keys: {list(response_data.keys())}")
            return None
        
        if content:
            # Debug: log the raw response
            logger.debug(f"Raw Llama response: {content[:200]}...")
            
            # Clean up response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON, trying to extract JSON from text: {e}")
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        logger.error(f"Could not parse extracted JSON: {json_match.group()[:100]}...")
                        return None
                else:
                    logger.error(f"No JSON found in response: {content[:100]}...")
                    return None
            
            # Calculate composite Instagram score
            # Check if we have at least some required fields
            required_fields = ['technical_score', 'visual_appeal', 'engagement_score', 'uniqueness']
            missing_fields = [field for field in required_fields if field not in analysis]
            
            if missing_fields:
                logger.warning(f"Missing fields in Llama response: {missing_fields}")
                # Fill in missing fields with default values
                for field in missing_fields:
                    analysis[field] = 5.0  # Default middle score
            
            # Enhanced weighted composite score
            weights = {
                'technical_score': 0.15,
                'visual_appeal': 0.25,
                'engagement_score': 0.30,
                'uniqueness': 0.20,
                'story_potential': 0.10
            }
            
            composite_score = (
                analysis.get('technical_score', 5.0) * weights['technical_score'] +
                analysis.get('visual_appeal', 5.0) * weights['visual_appeal'] +
                analysis.get('engagement_score', 5.0) * weights['engagement_score'] +
                analysis.get('uniqueness', 5.0) * weights['uniqueness'] +
                analysis.get('story_potential', 5.0) * weights['story_potential']
            )
            analysis['composite_score'] = round(composite_score, 2)
            
            # Determine tier based on composite score
            if composite_score >= 8.5:
                tier = "premium"
            elif composite_score >= 7.5:
                tier = "excellent"
            elif composite_score >= 6.0:
                tier = "good"
            elif composite_score >= 4.0:
                tier = "average"
            else:
                tier = "poor"
            
            analysis['instagram_tier'] = tier
            
            # More selective Instagram worthy determination
            analysis['instagram_worthy'] = tier in ['premium', 'excellent'] or composite_score >= 7.0
            
            return analysis
        else:
            logger.warning(f"No valid content in Llama response. Response keys: {list(response_data.keys())}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Llama JSON response: {e}")
        _llama_rate_limiter.release(success=False)
        return None
    except Exception as e:
        logger.error(f"Llama analysis error: {e}")
        _llama_rate_limiter.release(success=False)
        return None

def analyze_batch_with_llama(image_paths: List[str], config: Config) -> List[Dict]:
    """Analyze multiple images efficiently with Llama API using optimized batching"""
    global _llama_rate_limiter
    
    if not config.llama.get("api_key"):
        logger.error("Llama API key not provided")
        return []
    
    # Initialize rate limiter if needed
    if _llama_rate_limiter is None:
        _llama_rate_limiter = LlamaRateLimiter(config)
    
    # Get optimal batch size
    optimal_batch_size = _llama_rate_limiter.get_optimal_batch_size()
    
    logger.info(f"Llama batch analysis: {len(image_paths)} images, batch size: {optimal_batch_size}")
    
    results = []
    
    # Process in optimal batches
    for i in range(0, len(image_paths), optimal_batch_size):
        batch_paths = image_paths[i:i + optimal_batch_size]
        
        # Process batch concurrently
        with ThreadPoolExecutor(max_workers=min(len(batch_paths), 8)) as executor:
            futures = []
            
            for path in batch_paths:
                # Encode image
                base64_image = encode_image_to_base64(path, config)
                if base64_image:
                    future = executor.submit(analyze_with_llama, base64_image, config)
                    futures.append((future, path))
            
            # Collect results
            for future, path in futures:
                try:
                    result = future.result(timeout=60)
                    if result:
                        results.append({
                            'path': path,
                            'analysis': result,
                            'datetime': get_exif_datetime(path)
                        })
                except Exception as e:
                    logger.error(f"Batch analysis failed for {os.path.basename(path)}: {e}")
        
        # Small delay between batches to be respectful
        if i + optimal_batch_size < len(image_paths):
            time.sleep(0.1)
    
    logger.info(f"Llama batch analysis complete: {len(results)}/{len(image_paths)} successful")
    return results

def analyze_with_gemini(base64_image: str, config: Config) -> Optional[Dict]:
    """Analyze image using Gemini API with advanced Instagram scoring"""
    if not config.gemini["api_key"]:
        logger.error("Gemini API key not provided")
        return None
    
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
    
    url = f"{config.gemini['api_url']}/{config.gemini['model']}:generateContent"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt_text},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": config.gemini["api_key"]
    }
    
    try:
        response_data = make_rate_limited_request(url, payload, headers, config, "individual")
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            content = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Debug: log the raw response
            logger.debug(f"Raw Gemini response: {content[:200]}...")
            
            # Clean up response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON, trying to extract JSON from text: {e}")
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        logger.error(f"Could not parse extracted JSON: {json_match.group()[:100]}...")
                        return None
                else:
                    logger.error(f"No JSON found in response: {content[:100]}...")
                    return None
            
            # Calculate composite Instagram score
            # Check if we have at least some required fields
            required_fields = ['technical_score', 'visual_appeal', 'engagement_score', 'uniqueness']
            missing_fields = [field for field in required_fields if field not in analysis]
            
            if missing_fields:
                logger.warning(f"Missing fields in Gemini response: {missing_fields}")
                # Fill in missing fields with default values
                for field in missing_fields:
                    analysis[field] = 5.0  # Default middle score
            
            # Enhanced weighted composite score
            weights = {
                'technical_score': 0.15,
                'visual_appeal': 0.25,
                'engagement_score': 0.30,
                'uniqueness': 0.20,
                'story_potential': 0.10
            }
            
            composite_score = (
                analysis.get('technical_score', 5.0) * weights['technical_score'] +
                analysis.get('visual_appeal', 5.0) * weights['visual_appeal'] +
                analysis.get('engagement_score', 5.0) * weights['engagement_score'] +
                analysis.get('uniqueness', 5.0) * weights['uniqueness'] +
                analysis.get('story_potential', 5.0) * weights['story_potential']
            )
            analysis['composite_score'] = round(composite_score, 2)
            
            # Determine tier based on composite score
            if composite_score >= 8.5:
                tier = "premium"
            elif composite_score >= 7.5:
                tier = "excellent"
            elif composite_score >= 6.0:
                tier = "good"
            elif composite_score >= 4.0:
                tier = "average"
            else:
                tier = "poor"
            
            analysis['instagram_tier'] = tier
            
            # More selective Instagram worthy determination
            analysis['instagram_worthy'] = tier in ['premium', 'excellent'] or composite_score >= 7.0
            
            return analysis
        else:
            logger.warning("No candidates in Gemini response")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini analysis error: {e}")
        return None

def generate_post_content(post_images: List[str], config: Config) -> Optional[Dict]:
    """Generate captions and hashtags for a set of images"""
    logger.info(f"Generating content for {len(post_images)} images using {config.ai_provider}")
    
    base64_images = []
    for img_path in post_images:
        encoded = encode_image_to_base64(img_path)
        if encoded:
            base64_images.append(encoded)
    
    if not base64_images:
        return None
    
    if config.ai_provider == 'gemini':
        return generate_content_with_gemini(base64_images, config)
    elif config.ai_provider == 'llama':
        return generate_content_with_llama(base64_images, config)
    else:
        return generate_content_with_ollama(base64_images, config)

def generate_content_with_ollama(base64_images: List[str], config: Config) -> Optional[Dict]:
    """Generate content using Ollama"""
    prompt_text = """You are a creative social media manager. Generate a JSON object with these keys:
    1. "caption_options": A list of 3 different, engaging Instagram caption ideas
    2. "hashtags": A list of 15-20 relevant hashtags without the # symbol
    3. "post_theme": A brief description of the overall theme
    Return only the raw JSON object."""
    
    payload = {
        "model": config.ollama["model"],
        "prompt": prompt_text,
        "images": base64_images,
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 4096}
    }
    
    try:
        response = requests.post(config.ollama["api_url"], json=payload, timeout=300)
        response.raise_for_status()
        
        response_data = response.json()
        content = json.loads(response_data.get("response", "{}"))
        
        if "caption_options" in content and "hashtags" in content:
            return content
        else:
            return None
            
    except Exception as e:
        logger.error(f"Ollama content generation error: {e}")
        return None

def generate_content_with_llama(base64_images: List[str], config: Config) -> Optional[Dict]:
    """Generate content using Llama API with optimized processing"""
    global _llama_rate_limiter
    
    if not config.llama.get("api_key"):
        logger.error("Llama API key not provided. Set LLAMA_API_KEY environment variable or update config.")
        return None
    
    # Initialize rate limiter if needed
    if _llama_rate_limiter is None:
        _llama_rate_limiter = LlamaRateLimiter(config)
    
    # Llama API has a 9 attachment limit - truncate if necessary
    if len(base64_images) > 9:
        logger.warning(f"Llama API supports max 9 images, truncating from {len(base64_images)} to 9")
        base64_images = base64_images[:9]
    
    prompt_text = """You are a creative social media manager. Looking at these images, generate a JSON object with these exact keys:
    1. "caption_options": A list of 3 different, engaging Instagram caption ideas
    2. "hashtags": A list of 15-20 relevant hashtags without the # symbol
    3. "post_theme": A brief description of the overall theme
    
    Return ONLY the JSON object, no other text."""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.llama.get('api_key') or os.environ.get('LLAMA_API_KEY')}"
    }
    
    # Build content array with text and images
    content = [
        {
            "type": "text",
            "text": prompt_text
        }
    ]
    
    for base64_image in base64_images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    
    payload = {
        "model": config.llama["model"],
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }
    
    # Use rate limiting for content generation too
    try:
        _llama_rate_limiter.acquire()
    except Exception as e:
        logger.error(f"Rate limiter blocked content generation request: {e}")
        return None
    
    try:
        # Use optimized timeout for content generation
        timeout = config.llama.get('performance', {}).get('fast_timeout', 45)
        
        # Add retry logic for 500 errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    config.llama["api_url"], 
                    headers=headers, 
                    json=payload, 
                    timeout=timeout
                )
                
                if response.status_code == 500 and attempt < max_retries - 1:
                    # Server error - wait and retry
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.warning(f"Llama content API 500 error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                break
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Llama content API request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        response_data = response.json()
        _llama_rate_limiter.release(success=True)
        
        # Debug: log the actual response structure
        logger.debug(f"Llama content API response keys: {list(response_data.keys())}")
        
        # Handle Llama API response format
        content_text = None
        if 'completion_message' in response_data and 'content' in response_data['completion_message']:
            # Llama API format: completion_message.content.text
            content_obj = response_data['completion_message']['content']
            if isinstance(content_obj, dict) and 'text' in content_obj:
                content_text = content_obj['text']
            elif isinstance(content_obj, str):
                content_text = content_obj
        elif 'choices' in response_data and len(response_data['choices']) > 0:
            # OpenAI format (fallback)
            content_text = response_data['choices'][0]['message']['content']
        else:
            logger.warning(f"Unexpected Llama content response format. Keys: {list(response_data.keys())}")
            return None
        
        if content_text:
            
            # Clean up response
            content_text = content_text.strip()
            if content_text.startswith('```json'):
                content_text = content_text[7:]
            if content_text.endswith('```'):
                content_text = content_text[:-3]
            content_text = content_text.strip()
            
            parsed_content = json.loads(content_text)
            
            if "caption_options" in parsed_content and "hashtags" in parsed_content:
                return parsed_content
            else:
                return None
        else:
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Llama content JSON: {e}")
        _llama_rate_limiter.release(success=False)
        return None
    except Exception as e:
        logger.error(f"Llama content generation error: {e}")
        _llama_rate_limiter.release(success=False)
        return None

def generate_content_with_gemini(base64_images: List[str], config: Config) -> Optional[Dict]:
    """Generate content using Gemini API"""
    if not config.gemini["api_key"]:
        logger.error("Gemini API key not provided")
        return None
    
    prompt_text = """You are a creative social media manager. Looking at these images, generate a JSON object with these exact keys:
    1. "caption_options": A list of 3 different, engaging Instagram caption ideas
    2. "hashtags": A list of 15-20 relevant hashtags without the # symbol
    3. "post_theme": A brief description of the overall theme
    
    Return ONLY the JSON object, no other text."""
    
    url = f"{config.gemini['api_url']}/{config.gemini['model']}:generateContent"
    
    parts = [{"text": prompt_text}]
    for base64_image in base64_images:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64_image
            }
        })
    
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": config.gemini["api_key"]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        
        response_data = response.json()
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            content = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            parsed_content = json.loads(content)
            
            if "caption_options" in parsed_content and "hashtags" in parsed_content:
                return parsed_content
            else:
                return None
        else:
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini content JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini content generation error: {e}")
        return None

def save_post_content(post_dir: str, content: Dict, post_name: str, config: Config, images: List[str] = None) -> None:
    """Save post content to files"""
    try:
        # Optimize hashtags if enabled
        if config.enable_hashtag_optimization and images:
            optimizer = HashtagOptimizer()
            theme = content.get('post_theme', '')
            location = content.get('location', '')
            optimized_hashtags = optimizer.optimize_hashtags(content.get('hashtags', []), theme, location)
            content['hashtags'] = optimized_hashtags
        
        with open(os.path.join(post_dir, "captions.txt"), "w", encoding='utf-8') as f:
            f.write(f"=== {post_name.upper()} ===\n\n")
            
            if "post_theme" in content:
                f.write(f"THEME: {content['post_theme']}\n\n")
            
            f.write("--- CAPTION OPTIONS ---\n\n")
            for c_idx, cap in enumerate(content.get("caption_options", []), 1):
                f.write(f"{c_idx}. {cap}\n\n")
            
            f.write("--- HASHTAGS ---\n\n")
            hashtags = content.get("hashtags", [])
            formatted_hashtags = " ".join([f"#{tag.strip('#')}" for tag in hashtags])
            f.write(formatted_hashtags)
        
        # Create multi-platform variants if enabled
        if config.enable_multi_platform and images:
            create_platform_variants(post_dir, images, content)
            
        logger.info(f"Saved content for {post_name}")
        
    except Exception as e:
        logger.error(f"Could not save content for {post_name}: {e}")

def organize_photos_enhanced(analyzed_data: List[Dict], config: Config) -> None:
    """Enhanced photo organization with smart categorization and diversity optimization"""
    logger.info("Organizing photos with enhanced algorithm...")
    
    # Categorize photos by quality tiers
    photo_tiers = {
        'premium': [],
        'excellent': [],
        'good': [],
        'average': [],
        'poor': []
    }
    
    for data in analyzed_data:
        if data and data['analysis']:
            tier = data['analysis'].get('instagram_tier', 'average')
            composite_score = data['analysis'].get('composite_score', 0)
            
            # Enhanced categorization
            data['enhanced'] = {
                'tier': tier,
                'composite_score': composite_score,
                'category': data['analysis'].get('category', 'unknown'),
                'mood': data['analysis'].get('mood', 'neutral'),
                'setting': determine_setting(data['analysis']),
                'time_of_day': determine_time_of_day(data['analysis']),
                'people_count': determine_people_count(data['analysis'])
            }
            
            photo_tiers[tier].append(data)
    
    # Log tier distribution
    for tier, photos in photo_tiers.items():
        logger.info(f"{tier.capitalize()} photos: {len(photos)}")
    
    # Only use premium, excellent, and good photos
    worthy_photos = photo_tiers['premium'] + photo_tiers['excellent'] + photo_tiers['good']
    
    if not worthy_photos:
        logger.warning("No high-quality Instagram-worthy photos found.")
        return
    
    logger.info(f"Found {len(worthy_photos)} high-quality photos for posting")
    
    Path(config.output_folder).mkdir(parents=True, exist_ok=True)
    
    # Strategy 1: Premium showcase posts (best of the best)
    premium_posts = create_premium_posts(photo_tiers['premium'], config)
    
    # Strategy 2: Diverse excellence posts (mixed high-quality)
    diverse_posts = create_diverse_posts(photo_tiers['excellent'] + photo_tiers['premium'], config)
    
    # Strategy 3: Theme-based posts (category groupings)
    theme_posts = create_theme_posts(worthy_photos, config)
    
    # Strategy 4: Chronological posts (remaining photos)
    remaining_photos = get_remaining_photos(worthy_photos, premium_posts + diverse_posts + theme_posts)
    chrono_posts = create_chronological_posts(remaining_photos, config)
    
    # Save all posts
    all_posts = {
        'Premium_Showcase': premium_posts,
        'Diverse_Excellence': diverse_posts,
        'Theme_Based': theme_posts,
        'Chronological': chrono_posts
    }
    
    total_posts = 0
    for post_type, posts in all_posts.items():
        if posts:
            save_post_collection(posts, post_type, config)
            total_posts += len(posts)
    
    # Generate analytics report
    generate_analytics_report(worthy_photos, all_posts, config)
    
    logger.info(f"Enhanced organization complete! Created {total_posts} optimized posts")

def determine_setting(analysis: Dict) -> str:
    """Determine photo setting from analysis"""
    location = (analysis.get('location') or '').lower()
    category = (analysis.get('category') or '').lower()
    
    if any(word in location for word in ['indoor', 'inside', 'room', 'kitchen', 'restaurant']):
        return 'indoor'
    elif any(word in location for word in ['city', 'urban', 'street', 'building']):
        return 'urban'
    elif any(word in location for word in ['nature', 'forest', 'mountain', 'beach', 'lake']):
        return 'nature'
    else:
        return 'outdoor'

def determine_time_of_day(analysis: Dict) -> str:
    """Determine time of day from analysis"""
    strengths = ' '.join(analysis.get('strengths') or []).lower()
    location = (analysis.get('location') or '').lower()
    time_indicators = (analysis.get('time_of_day_indicators') or '').lower()
    
    combined_text = strengths + location + time_indicators
    
    if any(word in combined_text for word in ['golden hour', 'sunset', 'sunrise']):
        return 'golden_hour'
    elif any(word in combined_text for word in ['blue hour', 'twilight', 'dusk']):
        return 'blue_hour'
    elif any(word in combined_text for word in ['night', 'dark', 'evening']):
        return 'night'
    elif any(word in combined_text for word in ['bright', 'midday', 'noon']):
        return 'midday'
    else:
        return 'unknown'

def determine_people_count(analysis: Dict) -> int:
    """Determine number of people from analysis"""
    people_present = analysis.get('people_present', '0')
    category = (analysis.get('category') or '').lower()
    subcategory = (analysis.get('subcategory') or '').lower()
    
    if isinstance(people_present, str):
        if '6+' in people_present or 'many' in people_present.lower():
            return 6
        elif '2-5' in people_present:
            return 3
        elif '1' in people_present:
            return 1
        else:
            return 0
    
    return int(people_present) if isinstance(people_present, (int, float)) else 0

def create_premium_posts(premium_photos: List[Dict], config: Config) -> List[List[Dict]]:
    """Create posts from premium photos only"""
    if len(premium_photos) < config.post_size:
        return []
    
    # Sort by composite score
    premium_photos.sort(key=lambda x: x['enhanced']['composite_score'], reverse=True)
    
    posts = []
    max_premium_posts = min(3, len(premium_photos) // config.post_size)  # Max 3 premium posts
    
    for i in range(max_premium_posts):
        start_idx = i * config.post_size
        end_idx = start_idx + config.post_size
        post_photos = premium_photos[start_idx:end_idx]
        
        if len(post_photos) == config.post_size:
            posts.append(post_photos)
    
    logger.info(f"Created {len(posts)} premium showcase posts")
    return posts

def create_diverse_posts(photos: List[Dict], config: Config) -> List[List[Dict]]:
    """Create posts optimized for diversity"""
    if len(photos) < config.post_size:
        return []
    
    posts = []
    available_photos = photos.copy()
    max_diverse_posts = min(5, len(photos) // config.post_size)  # Max 5 diverse posts
    
    for _ in range(max_diverse_posts):
        if len(available_photos) < config.post_size:
            break
        
        post = select_diverse_photo_set(available_photos, config.post_size)
        if post:
            posts.append(post)
            # Remove selected photos
            available_photos = [p for p in available_photos if p not in post]
    
    logger.info(f"Created {len(posts)} diverse excellence posts")
    return posts

def select_diverse_photo_set(photos: List[Dict], post_size: int) -> List[Dict]:
    """Select a diverse set of photos for one post"""
    if len(photos) < post_size:
        return []
    
    # Start with highest scoring photo
    selected = [max(photos, key=lambda p: p['enhanced']['composite_score'])]
    remaining = [p for p in photos if p != selected[0]]
    
    # Select remaining photos to maximize diversity
    while len(selected) < post_size and remaining:
        best_photo = None
        best_diversity_score = -1
        
        for candidate in remaining:
            diversity_score = calculate_diversity_score(selected, candidate)
            if diversity_score > best_diversity_score:
                best_diversity_score = diversity_score
                best_photo = candidate
        
        if best_photo:
            selected.append(best_photo)
            remaining.remove(best_photo)
    
    return selected

def calculate_diversity_score(selected_photos: List[Dict], candidate: Dict) -> float:
    """Calculate how much diversity a candidate photo adds"""
    if not selected_photos:
        return candidate['enhanced']['composite_score']
    
    # Category diversity
    selected_categories = [p['enhanced']['category'] for p in selected_photos]
    category_diversity = 1.0 if candidate['enhanced']['category'] not in selected_categories else 0.3
    
    # Mood diversity
    selected_moods = [p['enhanced']['mood'] for p in selected_photos]
    mood_diversity = 1.0 if candidate['enhanced']['mood'] not in selected_moods else 0.5
    
    # Time diversity
    selected_times = [p['enhanced']['time_of_day'] for p in selected_photos]
    time_diversity = 1.0 if candidate['enhanced']['time_of_day'] not in selected_times else 0.4
    
    # Setting diversity
    selected_settings = [p['enhanced']['setting'] for p in selected_photos]
    setting_diversity = 1.0 if candidate['enhanced']['setting'] not in selected_settings else 0.6
    
    # Quality consistency (prefer similar quality levels)
    avg_quality = sum(p['enhanced']['composite_score'] for p in selected_photos) / len(selected_photos)
    quality_consistency = 1.0 - abs(candidate['enhanced']['composite_score'] - avg_quality) / 10.0
    
    # Weighted diversity score
    diversity_weights = {
        'category_diversity': 0.3,
        'mood_diversity': 0.2,
        'time_diversity': 0.2,
        'setting_diversity': 0.15,
        'quality_consistency': 0.15
    }
    
    diversity_score = (
        category_diversity * diversity_weights['category_diversity'] +
        mood_diversity * diversity_weights['mood_diversity'] +
        time_diversity * diversity_weights['time_diversity'] +
        setting_diversity * diversity_weights['setting_diversity'] +
        quality_consistency * diversity_weights['quality_consistency']
    )
    
    # Boost by photo quality
    return diversity_score * (candidate['enhanced']['composite_score'] / 10.0)

def create_theme_posts(photos: List[Dict], config: Config) -> List[List[Dict]]:
    """Create posts based on themes/categories"""
    from collections import defaultdict
    
    # Group by primary category
    category_groups = defaultdict(list)
    for photo in photos:
        category = photo['enhanced']['category']
        category_groups[category].append(photo)
    
    theme_posts = []
    
    # Create posts for categories with enough photos
    for category, category_photos in category_groups.items():
        if len(category_photos) >= config.post_size:
            # Sort by quality
            category_photos.sort(key=lambda p: p['enhanced']['composite_score'], reverse=True)
            
            # Create one theme post per category (best photos only)
            post_photos = category_photos[:config.post_size]
            theme_posts.append(post_photos)
    
    logger.info(f"Created {len(theme_posts)} theme-based posts")
    return theme_posts

def create_chronological_posts(photos: List[Dict], config: Config) -> List[List[Dict]]:
    """Create chronological posts from remaining photos"""
    if len(photos) < config.post_size:
        return []
    
    # Sort by date
    photos.sort(key=lambda p: p['datetime'])
    
    posts = []
    for i in range(0, len(photos), config.post_size):
        post_photos = photos[i:i + config.post_size]
        if len(post_photos) == config.post_size:
            posts.append(post_photos)
    
    logger.info(f"Created {len(posts)} chronological posts")
    return posts

def get_remaining_photos(all_photos: List[Dict], used_posts: List[List[Dict]]) -> List[Dict]:
    """Get photos not used in any post yet"""
    used_photos = set()
    for post in used_posts:
        for photo in post:
            used_photos.add(photo['path'])
    
    return [photo for photo in all_photos if photo['path'] not in used_photos]

def save_post_collection(posts: List[List[Dict]], post_type: str, config: Config) -> None:
    """Save a collection of posts"""
    if not posts:
        return
    
    collection_dir = os.path.join(config.output_folder, post_type)
    Path(collection_dir).mkdir(parents=True, exist_ok=True)
    
    for i, post_photos in enumerate(posts, 1):
        post_name = f"{post_type}_Post_{i}"
        post_dir = os.path.join(collection_dir, post_name)
        Path(post_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating {post_type.lower()} post: {post_name}")
        
        # Copy photos
        final_paths = []
        for idx, photo_data in enumerate(post_photos):
            original_path = photo_data['path']
            new_filename = f"{idx+1:02d}_{os.path.basename(original_path)}"
            destination_path = os.path.join(post_dir, new_filename)
            
            shutil.copy2(original_path, destination_path)
            final_paths.append(destination_path)
        
        # Generate content
        content = generate_post_content(final_paths, config)
        if content:
            # Add post strategy info
            content['post_strategy'] = {
                'type': post_type,
                'photo_tiers': [p['enhanced']['tier'] for p in post_photos],
                'categories': [p['enhanced']['category'] for p in post_photos],
                'avg_score': sum(p['enhanced']['composite_score'] for p in post_photos) / len(post_photos)
            }
            save_post_content(post_dir, content, post_name, config, final_paths)

def generate_analytics_report(photos: List[Dict], posts: Dict, config: Config) -> None:
    """Generate comprehensive analytics report"""
    analytics_dir = os.path.join(config.output_folder, "Analytics")
    Path(analytics_dir).mkdir(parents=True, exist_ok=True)
    
    report = {
        'summary': {
            'total_photos_analyzed': len(photos),
            'total_posts_created': sum(len(post_list) for post_list in posts.values()),
            'photos_used': sum(len(post_list) * config.post_size for post_list in posts.values()),
            'avg_composite_score': sum(p['enhanced']['composite_score'] for p in photos) / len(photos) if photos else 0
        },
        'tier_distribution': {},
        'category_distribution': {},
        'post_strategies': {}
    }
    
    # Tier distribution
    from collections import Counter
    tiers = [p['enhanced']['tier'] for p in photos]
    report['tier_distribution'] = dict(Counter(tiers))
    
    # Category distribution
    categories = [p['enhanced']['category'] for p in photos]
    report['category_distribution'] = dict(Counter(categories))
    
    # Post strategies
    for strategy, post_list in posts.items():
        if post_list:
            report['post_strategies'][strategy] = {
                'count': len(post_list),
                'photos_per_post': config.post_size,
                'total_photos': len(post_list) * config.post_size
            }
    
    # Save report
    with open(os.path.join(analytics_dir, "enhanced_analytics.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    # Save readable report
    with open(os.path.join(analytics_dir, "analytics_report.txt"), "w") as f:
        f.write("=== ENHANCED INSTAGRAM ANALYTICS REPORT ===\n\n")
        f.write(f"Total Photos Analyzed: {report['summary']['total_photos_analyzed']}\n")
        f.write(f"Total Posts Created: {report['summary']['total_posts_created']}\n")
        f.write(f"Photos Used: {report['summary']['photos_used']}\n")
        f.write(f"Average Quality Score: {report['summary']['avg_composite_score']:.2f}/10\n\n")
        
        f.write("QUALITY TIER DISTRIBUTION:\n")
        for tier, count in report['tier_distribution'].items():
            percentage = (count / len(photos)) * 100
            f.write(f"  {tier.capitalize()}: {count} photos ({percentage:.1f}%)\n")
        
        f.write("\nCATEGORY DISTRIBUTION:\n")
        for category, count in sorted(report['category_distribution'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(photos)) * 100
            f.write(f"  {category.capitalize()}: {count} photos ({percentage:.1f}%)\n")
        
        f.write("\nPOST STRATEGIES:\n")
        for strategy, info in report['post_strategies'].items():
            f.write(f"  {strategy}: {info['count']} posts ({info['total_photos']} photos)\n")
    
    logger.info("Analytics report generated")

# Keep the original function for backward compatibility
def organize_photos(analyzed_data: List[Dict], config: Config) -> None:
    """Original organize photos function - now calls enhanced version"""
    organize_photos_enhanced(analyzed_data, config)

def get_image_files(source_folder: str) -> List[str]:
    """Get all supported image files from source folder"""
    if not os.path.exists(source_folder):
        raise FileNotFoundError(f"Source folder '{source_folder}' not found")
    
    image_files = []
    for filename in os.listdir(source_folder):
        if filename.lower().endswith(SUPPORTED_FORMATS):
            image_files.append(os.path.join(source_folder, filename))
    
    logger.info(f"Found {len(image_files)} image files")
    return image_files

def main():
    """Main function"""
    try:
        # Parse arguments and setup config
        args = setup_cli_args()
        config = Config(args.config)
        config.update_from_args(args)
        
        logger.info("Starting Instagram photo organizer...")
        logger.info(f"Mode: {'Simple' if args.simple_mode else 'Advanced'}")
        logger.info(f"AI Provider: {config.ai_provider}")
        logger.info(f"Source folder: {config.source_folder}")
        logger.info(f"Output folder: {config.output_folder}")
        logger.info(f"Development mode: {'ON' if not config.process_all else 'OFF'}")
        
        # Validate setup
        if config.ai_provider == 'gemini' and not config.gemini["api_key"]:
            logger.error("Gemini API key required. Use --gemini-key or set in config file.")
            return
        
        # Get image files
        all_source_paths = get_image_files(config.source_folder)
        if not all_source_paths:
            logger.error("No supported image files found")
            return
        
        # Filter similar images
        unique_source_paths = filter_similar_images(all_source_paths, config.similarity_threshold, config)
        
        # Convert and prepare images (optimized - no unnecessary conversions)
        processing_folder, image_paths_in_temp = convert_and_prepare_images(
            config.source_folder, 
            config.temp_convert_folder, 
            unique_source_paths,
            config.image_quality
        )
        
        # Enhance images if enabled
        if config.enable_enhancement:
            logger.info("Enhancing images...")
            enhanced_dir = os.path.join(config.temp_convert_folder, "enhanced")
            Path(enhanced_dir).mkdir(exist_ok=True)
            
            enhanced_paths = []
            for path in image_paths_in_temp:
                enhanced_path = os.path.join(enhanced_dir, os.path.basename(path))
                if auto_enhance_image(path, enhanced_path):
                    enhanced_paths.append(enhanced_path)
                else:
                    enhanced_paths.append(path)
            
            image_paths_in_temp = enhanced_paths
        
        # Get EXIF data and sort by date
        all_image_data = []
        for path in image_paths_in_temp:
            image_data = {
                'path': path,
                'datetime': get_exif_datetime(path)
            }
            all_image_data.append(image_data)
        
        all_image_data.sort(key=lambda x: x['datetime'])
        
        # Apply dev mode limit if needed
        if not config.process_all:
            limit = min(config.dev_mode_limit, len(all_image_data))
            logger.info(f"Development mode: Processing {limit} photos")
            image_data_to_process = all_image_data[:limit]
        else:
            image_data_to_process = all_image_data
        
        if not image_data_to_process:
            logger.error("No processable images found")
            return
        
        # Analyze images with AI using parallel processing
        image_paths = [data['path'] for data in image_data_to_process]
        
        # Choose analysis method based on configuration and provider
        if config.ai_provider == 'gemini' and config.ai_batch_size > 1 and len(image_paths) > config.ai_batch_size:
            logger.info(f"Using batch analysis with Gemini (batch size: {config.ai_batch_size})")
            final_analyzed_data = []
            
            # Process in batches
            total_batches = (len(image_paths) + config.ai_batch_size - 1) // config.ai_batch_size
            
            for i in range(0, len(image_paths), config.ai_batch_size):
                batch_paths = image_paths[i:i + config.ai_batch_size]
                batch_num = i // config.ai_batch_size + 1
                
                batch_results = analyze_batch_with_gemini(batch_paths, config)
                final_analyzed_data.extend(batch_results)
                
                logger.info(f"Completed batch {batch_num}/{total_batches}")
                
                # Add delay between batches to respect rate limits (except for last batch)
                if batch_num < total_batches:
                    delay = 2.0  # 2 second delay between batches
                    logger.debug(f"Waiting {delay}s before next batch...")
                    time.sleep(delay)
        else:
            # Use parallel individual analysis
            final_analyzed_data = analyze_images_parallel(image_paths, config)
        
        # Progress bar is handled within the analysis functions
        
        # Generate analytics if enabled
        if config.enable_analytics and final_analyzed_data:
            logger.info("Generating analytics...")
            analytics = analyze_photo_patterns(final_analyzed_data)
            
            analytics_dir = os.path.join(config.output_folder, "analytics")
            Path(analytics_dir).mkdir(parents=True, exist_ok=True)
            
            generate_analytics_report(analytics, os.path.join(analytics_dir, "report.txt"))
            create_analytics_visualizations(analytics, analytics_dir)
        
        # Apply contextual filtering after AI analysis
        if final_analyzed_data:
            logger.info(f"Successfully analyzed {len(final_analyzed_data)} images")
            
            # Filter contextually similar images using AI analysis
            if config.enable_contextual_filtering:
                final_analyzed_data = filter_contextually_similar_images(final_analyzed_data, config)
                logger.info(f"After contextual filtering: {len(final_analyzed_data)} unique context images")
            
            organize_photos(final_analyzed_data, config)
            
            # Generate posting schedule if enabled
            if config.enable_scheduling:
                logger.info("Generating posting schedule...")
                worthy_count = len([d for d in final_analyzed_data if d['analysis'].get('instagram_worthy', False)])
                num_posts = worthy_count // config.post_size
                
                if num_posts > 0:
                    schedule = generate_posting_schedule(num_posts)
                    schedule_path = os.path.join(config.output_folder, "posting_schedule.json")
                    
                    with open(schedule_path, 'w') as f:
                        json.dump(schedule, f, indent=2, default=str)
                    
                    logger.info(f"Saved posting schedule to {schedule_path}")
            
            logger.info("✅ Instagram photo organization complete!")
        else:
            logger.error(f"Could not analyze any photos. Check your {config.ai_provider} setup.")
        
        # Clean up temporary directory
        cleanup_temp_directory(processing_folder, keep_files=config.keep_temp_files)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        # Clean up on interrupt
        if 'processing_folder' in locals():
            cleanup_temp_directory(processing_folder, keep_files=config.keep_temp_files)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Clean up on error
        if 'processing_folder' in locals():
            cleanup_temp_directory(processing_folder, keep_files=config.keep_temp_files)
        raise

if __name__ == "__main__":
    main()