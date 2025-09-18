#!/usr/bin/env python3
"""
Setup script for Llama API integration
"""

import os
import json
import sys

def setup_llama_config():
    """Setup Llama API configuration"""
    
    print("🦙 Llama API Setup")
    print("=" * 40)
    
    # Check if config.json exists
    if not os.path.exists("config.json"):
        print("❌ config.json not found!")
        print("Please run this script from the project directory.")
        return False
    
    # Get API key from user
    api_key = input("Enter your Llama API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        return False
    
    try:
        # Load existing config
        with open("config.json", "r") as f:
            config = json.load(f)
        
        # Update Llama configuration
        if "llama" not in config:
            config["llama"] = {}
        
        config["llama"]["api_key"] = api_key
        config["ai_provider"] = "llama"
        
        # Save updated config
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration updated successfully!")
        print(f"✅ AI provider set to: llama")
        print(f"✅ API key configured")
        
        # Also set environment variable for current session
        os.environ["LLAMA_API_KEY"] = api_key
        print("✅ Environment variable set for current session")
        
        print("\n📝 To make the environment variable permanent, add this to your shell profile:")
        print(f"export LLAMA_API_KEY='{api_key}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def verify_setup():
    """Verify the setup is working"""
    print("\n🔍 Verifying setup...")
    
    try:
        # Try to import and run a basic test
        from test_llama_api import test_llama_api
        
        if test_llama_api():
            print("✅ Setup verification passed!")
            return True
        else:
            print("❌ Setup verification failed!")
            return False
            
    except ImportError:
        print("❌ Could not import test module")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("Setting up Llama API for Instagram Photo Organizer")
    
    if setup_llama_config():
        print("\n" + "=" * 40)
        
        # Ask if user wants to run verification
        verify = input("Would you like to verify the setup with a test? (y/n): ").strip().lower()
        
        if verify in ['y', 'yes']:
            verify_setup()
        
        print("\n🎉 Setup complete!")
        print("You can now run the Instagram organizer with Llama API:")
        print("python instagram_organizer.py --source your_photos_folder")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)