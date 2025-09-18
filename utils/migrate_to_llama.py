#!/usr/bin/env python3
"""
Migration script to switch from Gemini/Ollama to Llama API
"""

import os
import json
import sys

def migrate_config():
    """Migrate existing config to use Llama as default"""
    
    print("🦙 Migrating to Llama API")
    print("=" * 40)
    
    # Check if config exists
    if not os.path.exists("../config.json"):
        print("❌ config.json not found!")
        print("Please run this script from the project directory.")
        return False
    
    try:
        # Load existing config
        with open("../config.json", "r") as f:
            config = json.load(f)
        
        # Show current provider
        current_provider = config.get("ai_provider", "unknown")
        print(f"📋 Current AI provider: {current_provider}")
        
        # Get API key
        api_key = input("Enter your Llama API key: ").strip()
        
        if not api_key:
            print("❌ No API key provided!")
            return False
        
        # Create backup
        backup_file = "../config.json.backup"
        with open(backup_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Backup created: {backup_file}")
        
        # Update config
        config["ai_provider"] = "llama"
        
        # Add Llama configuration if not exists
        if "llama" not in config:
            config["llama"] = {}
        
        config["llama"].update({
            "api_key": api_key,
            "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
            "api_url": "https://api.llama.com/v1/chat/completions",
            "timeout": 120
        })
        
        # Save updated config
        with open("../config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration migrated successfully!")
        print(f"✅ AI provider changed: {current_provider} → llama")
        print(f"✅ Llama API key configured")
        
        # Set environment variable
        os.environ["LLAMA_API_KEY"] = api_key
        print("✅ Environment variable set for current session")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def show_migration_summary():
    """Show what changed in the migration"""
    print("\n📋 Migration Summary")
    print("=" * 40)
    print("✅ AI provider changed to Llama")
    print("✅ Llama API configuration added")
    print("✅ Backup created (config.json.backup)")
    print("✅ Environment variable set")
    
    print("\n🔄 Your previous provider settings are preserved:")
    print("   - You can still switch back using --ai-provider gemini/ollama")
    print("   - All existing configurations remain intact")
    
    print("\n📝 To make environment variable permanent:")
    api_key = os.environ.get("LLAMA_API_KEY", "your-api-key")
    print(f"   export LLAMA_API_KEY='{api_key}'")

def test_migration():
    """Test the migration by running a quick API test"""
    print("\n🧪 Testing migration...")
    
    try:
        from tests.test_llama_api import test_llama_api
        
        if test_llama_api():
            print("✅ Migration test passed!")
            return True
        else:
            print("❌ Migration test failed!")
            return False
            
    except ImportError:
        print("❌ Could not import test module")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("Migrating Instagram Photo Organizer to Llama API")
    
    if migrate_config():
        show_migration_summary()
        
        # Ask if user wants to test
        test = input("\nWould you like to test the migration? (y/n): ").strip().lower()
        
        if test in ['y', 'yes']:
            test_migration()
        
        print("\n🎉 Migration complete!")
        print("You can now run the organizer with Llama API:")
        print("python instagram_organizer.py --source your_photos_folder")
        
    else:
        print("\n❌ Migration failed!")
        print("Your original configuration is unchanged.")
        sys.exit(1)