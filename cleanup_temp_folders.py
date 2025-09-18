#!/usr/bin/env python3
"""
Utility script to clean up old temporary conversion folders
"""

import os
import shutil
import glob
from pathlib import Path
import argparse

def cleanup_temp_folders(base_temp_name: str = "temp_converted_images", dry_run: bool = False):
    """Clean up all temporary conversion folders"""
    
    # Find all temp directories matching the pattern
    temp_pattern = f"{base_temp_name}*"
    temp_dirs = glob.glob(temp_pattern)
    
    if not temp_dirs:
        print(f"No temporary directories found matching pattern: {temp_pattern}")
        return
    
    print(f"Found {len(temp_dirs)} temporary directories:")
    
    total_size = 0
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            # Calculate directory size
            dir_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(temp_dir)
                for filename in filenames
            )
            total_size += dir_size
            
            size_mb = dir_size / (1024 * 1024)
            file_count = sum(len(filenames) for _, _, filenames in os.walk(temp_dir))
            
            print(f"  📁 {temp_dir}: {file_count} files, {size_mb:.1f} MB")
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"\nTotal size: {total_size_mb:.1f} MB")
    
    if dry_run:
        print("\n🔍 DRY RUN - No files will be deleted")
        return
    
    # Confirm deletion
    response = input(f"\n❓ Delete all {len(temp_dirs)} temporary directories? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Delete directories
    deleted_count = 0
    for temp_dir in temp_dirs:
        try:
            shutil.rmtree(temp_dir)
            print(f"✅ Deleted: {temp_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {temp_dir}: {e}")
    
    print(f"\n🎉 Cleanup complete! Deleted {deleted_count}/{len(temp_dirs)} directories")
    print(f"💾 Freed up {total_size_mb:.1f} MB of disk space")

def list_temp_folders(base_temp_name: str = "temp_converted_images"):
    """List all temporary conversion folders without deleting"""
    
    temp_pattern = f"{base_temp_name}*"
    temp_dirs = glob.glob(temp_pattern)
    
    if not temp_dirs:
        print(f"No temporary directories found matching pattern: {temp_pattern}")
        return
    
    print(f"Found {len(temp_dirs)} temporary directories:")
    
    total_size = 0
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            # Get creation time
            creation_time = os.path.getctime(temp_dir)
            from datetime import datetime
            creation_date = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M")
            
            # Calculate directory size
            dir_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(temp_dir)
                for filename in filenames
            )
            total_size += dir_size
            
            size_mb = dir_size / (1024 * 1024)
            file_count = sum(len(filenames) for _, _, filenames in os.walk(temp_dir))
            
            print(f"  📁 {temp_dir}")
            print(f"     Created: {creation_date}")
            print(f"     Files: {file_count}, Size: {size_mb:.1f} MB")
            print()
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"Total size: {total_size_mb:.1f} MB")

def main():
    parser = argparse.ArgumentParser(description="Clean up temporary Instagram organizer folders")
    parser.add_argument("--list", "-l", action="store_true", 
                       help="List temporary folders without deleting")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be deleted without actually deleting")
    parser.add_argument("--base-name", "-b", default="temp_converted_images",
                       help="Base name for temporary folders (default: temp_converted_images)")
    
    args = parser.parse_args()
    
    print("🧹 Instagram Organizer Temp Folder Cleanup Utility\n")
    
    if args.list:
        list_temp_folders(args.base_name)
    else:
        cleanup_temp_folders(args.base_name, args.dry_run)

if __name__ == "__main__":
    main()