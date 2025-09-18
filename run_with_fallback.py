#!/usr/bin/env python3
"""
Robust Instagram Organizer Runner with Automatic Fallbacks
Handles Gemini API issues gracefully
"""

import subprocess
import sys
import time
import json
import os

def run_with_individual_analysis(source_folder, gemini_key, additional_args=None):
    """Run with individual analysis (more reliable for API issues)"""
    
    # Create a temporary config with individual analysis settings
    config = {
        "source_folder": source_folder,
        "ai_provider": "gemini",
        "gemini": {
            "api_key": gemini_key,
            "model": "gemini-2.0-flash-lite"
        },
        "processing": {
            "post_size": 10,
            "process_all": False,
            "dev_mode_limit": 100,
            "similarity_threshold": 2,
            "image_quality": 95,
            "keep_temp_files": False
        },
        "performance": {
            "ai_analysis": {
                "parallel_workers": 1,  # Single worker for reliability
                "batch_size": 1,        # Individual analysis only
                "max_retries": 10,      # More retries
                "timeout": 120,         # Longer timeout
                "rate_limit_delay": 8.0, # Longer delays
                "batch_delay": 10.0
            }
        }
    }
    
    # Save temporary config
    temp_config_path = "temp_reliable_config.json"
    with open(temp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("🔄 Running with reliable individual analysis settings...")
    print("⚡ This is slower but more reliable for API issues")
    
    # Build command
    cmd = [
        "python", "instagram_organizer.py",
        "--config", temp_config_path,
        "--gemini-key", gemini_key
    ]
    
    if additional_args:
        cmd.extend(additional_args)
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    finally:
        # Clean up temp config
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_with_fallback.py <source_folder> <gemini_key> [additional_args...]")
        print("Example: python run_with_fallback.py '/path/to/photos' 'your_api_key' --dev-mode --limit 50")
        sys.exit(1)
    
    source_folder = sys.argv[1]
    gemini_key = sys.argv[2]
    additional_args = sys.argv[3:] if len(sys.argv) > 3 else []
    
    print("🚀 Instagram Organizer - Reliable Runner")
    print(f"📁 Source: {source_folder}")
    print(f"🔑 Using Gemini API")
    
    # Try with reliable settings
    print("\n🔄 Attempting with reliable individual analysis...")
    success = run_with_individual_analysis(source_folder, gemini_key, additional_args)
    
    if success:
        print("\n✅ Successfully completed!")
    else:
        print("\n❌ Failed. Check the logs above for details.")
        print("\n💡 Troubleshooting tips:")
        print("1. Check your Gemini API key is valid")
        print("2. Verify your source folder path exists")
        print("3. Try with --dev-mode --limit 10 for testing")
        print("4. Wait a few minutes and try again (API may be temporarily overloaded)")

if __name__ == "__main__":
    main()