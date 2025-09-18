# 🚀 Setup Guide

## Quick Setup (5 minutes)

### 1. Install Python Dependencies

```bash
pip install pillow imagehash pillow-heif requests
```

### 2. Choose Your AI Provider

#### Option A: Gemini API (Recommended)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key

#### Option B: Ollama (Local)

```bash
# Install Ollama
brew install ollama  # macOS

# Start service
ollama serve

# Pull vision model
ollama pull gemma3:4b
```

### 3. Add Some Photos

Put your photos in the `source_photos` folder, or specify a different folder with `--source`.

### 4. Test the Setup

#### With Gemini

```bash
python instagram_organizer.py --ai-provider gemini --gemini-key YOUR_API_KEY --dev-mode --limit 3
```

#### With Ollama

```bash
python instagram_organizer.py --ai-provider ollama --dev-mode --limit 3
```

### 5. Configure Your Settings

Edit `config.json`:

```json
{
  "source_folder": "/path/to/your/photos",
  "ai_provider": "gemini",
  "gemini": {
    "api_key": "YOUR_API_KEY_HERE"
  }
}
```

### 6. Run Full Processing

```bash
python instagram_organizer.py --config config.json
```

## Advanced Setup (Optional Features)

### Install Additional Dependencies

```bash
pip install matplotlib seaborn opencv-python
```

### Enable Advanced Features

The script automatically detects available features. No additional setup needed!

## Troubleshooting

### Common Issues

- **"imagehash not found"**: Run `pip install imagehash`
- **"Gemini API key required"**: Add `--gemini-key YOUR_KEY`
- **"Ollama connection refused"**: Run `ollama serve`

### Getting Help

1. Check the error message in the terminal
2. Verify your API key or Ollama setup
3. Try with `--dev-mode --limit 3` first

That's it! You're ready to organize your photos. 📸
