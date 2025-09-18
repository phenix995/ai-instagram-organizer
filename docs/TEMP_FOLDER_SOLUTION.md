# 🧹 Temp Folder Management Solution

## Problem Fixed

The `temp_converted_images` folder was accumulating photos from previous runs when switching to new source folders, causing:

- Old photos being included in new analysis runs
- Wasted processing time on irrelevant images
- Confusion about which photos belong to which source folder
- Disk space waste from accumulated temp files

## ✅ Solution Implemented

### 1. **Unique Temp Directories**

Each source folder now gets its own unique temp directory:

```
temp_converted_images_a1b2c3d4/  # For /path/to/photos1
temp_converted_images_e5f6g7h8/  # For /path/to/photos2
```

The system creates a hash from the source folder path to ensure uniqueness.

### 2. **Automatic Cleanup**

- Temp directories are automatically cleaned up after processing
- Configurable via `keep_temp_files` setting in config.json
- Cleanup happens on normal completion, interruption, and errors

### 3. **Fresh Start Every Run**

- Each run starts with a clean temp directory
- No old converted files interfere with new analysis
- Guaranteed isolation between different source folders

## 🔧 Configuration

### In `config.json`

```json
{
  "processing": {
    "keep_temp_files": false  // Set to true to keep temp files for debugging
  }
}
```

### Behavior

- `keep_temp_files: false` (default) - Automatically delete temp files after processing
- `keep_temp_files: true` - Keep temp files for inspection/debugging

## 🛠️ Manual Cleanup Utility

Use the provided cleanup utility for manual management:

### List all temp folders

```bash
python cleanup_temp_folders.py --list
```

### Clean up all temp folders (with confirmation)

```bash
python cleanup_temp_folders.py
```

### Dry run (see what would be deleted)

```bash
python cleanup_temp_folders.py --dry-run
```

### Clean specific pattern

```bash
python cleanup_temp_folders.py --base-name "temp_converted_images"
```

## 📋 What Changed

### 1. **Enhanced `convert_and_prepare_images()` function:**

- Creates unique temp directory based on source folder hash
- Automatically cleans existing temp directory before starting
- Returns the unique temp directory path

### 2. **New `cleanup_temp_directory()` function:**

- Handles safe cleanup of temp directories
- Respects `keep_temp_files` configuration
- Provides logging for cleanup operations

### 3. **Updated `main()` function:**

- Automatic cleanup after successful processing
- Cleanup on keyboard interrupt (Ctrl+C)
- Cleanup on errors/exceptions
- Uses configuration setting for cleanup behavior

### 4. **New cleanup utility script:**

- `cleanup_temp_folders.py` for manual temp folder management
- Lists temp folders with size and creation date
- Safe deletion with confirmation prompts
- Dry-run capability for safety

## 🎯 Benefits

1. **No More Cross-Contamination**: Each source folder is processed in isolation
2. **Automatic Cleanup**: No manual intervention needed for temp file management
3. **Disk Space Management**: Automatic cleanup prevents disk space waste
4. **Debugging Support**: Option to keep temp files when needed
5. **Manual Control**: Utility script for advanced temp folder management
6. **Error Recovery**: Cleanup happens even if processing fails

## 🚀 Usage Examples

### Normal usage (auto-cleanup)

```bash
python instagram_organizer.py --source "/path/to/hawaii_photos" --gemini-key YOUR_KEY
# Temp files automatically cleaned up after processing
```

### Keep temp files for debugging

```bash
# Set keep_temp_files: true in config.json, then:
python instagram_organizer.py --source "/path/to/photos" --gemini-key YOUR_KEY
# Temp files kept for inspection
```

### Switch between different photo collections

```bash
# First collection
python instagram_organizer.py --source "/path/to/vacation_photos" --gemini-key YOUR_KEY

# Second collection (completely isolated)
python instagram_organizer.py --source "/path/to/wedding_photos" --gemini-key YOUR_KEY

# No interference between collections!
```

### Manual cleanup when needed

```bash
# See what temp folders exist
python cleanup_temp_folders.py --list

# Clean them up
python cleanup_temp_folders.py
```

## 🔍 Verification

To verify the fix is working:

1. **Run with first source folder:**

   ```bash
   python instagram_organizer.py --source "/path/to/photos1" --gemini-key YOUR_KEY
   ```

2. **Check temp directory created:**

   ```bash
   ls -la temp_converted_images_*
   ```

3. **Run with different source folder:**

   ```bash
   python instagram_organizer.py --source "/path/to/photos2" --gemini-key YOUR_KEY
   ```

4. **Verify isolation:**
   - Each run should create its own temp directory
   - No old photos should appear in new analysis
   - Temp directories should be cleaned up automatically (unless `keep_temp_files: true`)

This solution ensures complete isolation between different photo collections and prevents the accumulation of old temp files! 🎉
