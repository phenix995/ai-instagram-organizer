# 📸 AI Instagram Organizer

An AI-powered tool that automatically organizes your photos into Instagram-ready posts with smart captions, optimized hashtags, and multi-platform content generation.

## ✨ Features

### 🤖 **AI-Powered Analysis**

- Supports **Llama** (cloud, default), **Ollama** (local), and **Gemini** (cloud) AI providers
- Analyzes photos for Instagram worthiness and quality scoring
- Generates engaging captions with photo-specific references
- Smart hashtag generation and optimization
- Advanced computer vision quality analysis (optional)
- Instagram engagement prediction modeling

### 📅 **Smart Organization**

- Chronological post creation based on photo dates
- Highlights posts from remaining quality photos
- Configurable post sizes (default: 10 photos per post)
- Duplicate photo detection and removal
- Semantic context analysis for content diversity

### 🎨 **Advanced Features** (Optional)

- Auto-enhancement (brightness, contrast, saturation)
- Multiple format generation (square, story, reel)
- HEIC/HEIF to JPEG conversion
- Multi-platform content (Instagram, TikTok, Twitter, LinkedIn)
- Analytics and insights with visual charts
- Smart scheduling recommendations

### 🏷️ **Hashtag Intelligence**

- Competition-based hashtag categorization
- Trending hashtag integration
- Location-based hashtag generation
- Strategic mixing for optimal reach

### 🌐 **Multi-Platform Content**

- Instagram feed posts and stories
- TikTok/Reels video scripts
- Twitter thread generation
- LinkedIn professional posts

### ⏰ **Smart Scheduling**

- Optimal posting time recommendations
- Engagement-based scheduling
- Customizable posting intervals

## 🚀 Quick Start

### 🐳 Run with Docker

1. **Build and start the container** (uses Docker Compose):

   ```bash
   docker compose up --build
   ```

   By default this runs the organizer in development mode against photos mounted from `./photos` on your host. Override the host folder by setting the `HOST_PHOTO_DIR` variable before running Compose. On Windows you can supply a Windows-style path, for example `HOST_PHOTO_DIR=C:/Users/you/Pictures`.

2. **Provide API keys** by exporting them (or storing them in a `.env` file that Compose will read automatically):

   ```bash
   export LLAMA_API_KEY="your-api-key-here"
   export GEMINI_API_KEY="your-gemini-key"
   docker compose up
   ```

3. **Override runtime options** by appending flags to the Compose command. For example, to process a full photo library in simple mode:

   ```bash
   docker compose run organizer --source /data/photos --simple-mode
   ```

   All command-line arguments supported by `ai_instagram_organizer.py` can be passed this way.

### 🖥️ Run the Web Dashboard with Docker

The Compose file also includes a `webui` service that launches the FastAPI dashboard. It reuses the same environment variables
and volume mounts as the CLI container, so your API keys and mounted photo/config directories are available to the UI.

1. **Start the dashboard**:

   ```bash
   docker compose up webui
   ```

2. **Open the app** at [http://localhost:8000](http://localhost:8000). The container publishes port `8000` so the FastAPI UI is
   reachable from your browser.

3. **Customize paths if needed** by exporting `HOST_PHOTO_DIR` and `HOST_CONFIG_FILE` before running Compose. The same values
   used for the CLI are shared with the dashboard.

### Prerequisites

1. **Install Python dependencies**:

   ```bash
   pip install pillow imagehash pillow-heif requests
   ```

### Option 1: Llama API (Default - Recommended)

1. **Get Llama API Key**: Sign up at [Llama API](https://api.llama.com) and get your API key

2. **Quick Setup**:

   ```bash
   # Run setup script (new users)
   python utils/setup_llama.py

   # Or set environment variable manually
   export LLAMA_API_KEY="your-api-key-here"
   ```

3. **Run with Llama**:

   ```bash
   # Quick test
   python ai_instagram_organizer.py --dev-mode --limit 5

   # Full run
   python ai_instagram_organizer.py --source "/path/to/photos"
   ```

### Option 2: Gemini API (Alternative Cloud Option)

1. **Get Gemini API Key**: Go to [Google AI Studio](https://aistudio.google.com/app/apikey)

2. **Run with Gemini**:

   ```bash
   # Quick test
   python ai_instagram_organizer.py --ai-provider gemini --gemini-key YOUR_API_KEY --dev-mode --limit 5

   # Full run
   python ai_instagram_organizer.py --ai-provider gemini --gemini-key YOUR_API_KEY --source "/path/to/photos"
   ```

### Option 3: Ollama (Local AI)

1. **Setup Ollama**:

   ```bash
   # Install Ollama
   brew install ollama  # macOS

   # Start service
   ollama serve

   # Pull vision model
   ollama pull gemma3:4b
   ```

2. **Run with Ollama**:

   ```bash
   python ai_instagram_organizer.py --ai-provider ollama --source "/path/to/photos"
   ```

## 📋 Command Line Options

```bash
# Basic usage with Llama (default)
python ai_instagram_organizer.py --source "/path/to/photos"

# Basic usage with Gemini
python ai_instagram_organizer.py --ai-provider gemini --gemini-key YOUR_KEY

# Development mode (test with fewer photos)
python ai_instagram_organizer.py --dev-mode --limit 10

# Simple mode (core features only)
python ai_instagram_organizer.py --simple-mode

# Custom settings
python ai_instagram_organizer.py \
  --source "/path/to/photos" \
  --ai-provider llama \
  --llama-key YOUR_KEY \
  --post-size 8 \
  --similarity 5
```

### Available Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--source, -s` | Source folder path | From config |
| `--ai-provider` | AI provider (llama/ollama/gemini) | llama |
| `--llama-key` | Llama API key | None |
| `--gemini-key` | Gemini API key | None |
| `--dev-mode, -d` | Process fewer photos for testing | False |
| `--limit, -l` | Photo limit in dev mode | 100 |
| `--post-size, -p` | Photos per post | 10 |
| `--similarity` | Similarity threshold (0-10) | 3 |
| `--simple-mode` | Disable advanced features | False |
| `--config, -c` | Config file path | config.json |

## ⚙️ Configuration

### Config File (config.json)

```json
{
  "source_folder": "/path/to/your/photos",
  "ai_provider": "llama",
  "processing": {
    "post_size": 10,
    "process_all": false,
    "dev_mode_limit": 20,
    "similarity_threshold": 3
  },
  "llama": {
    "api_key": "YOUR_LLAMA_API_KEY_HERE",
    "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
    "api_url": "https://api.llama.com/v1/chat/completions"
  },
  "gemini": {
    "api_key": "YOUR_GEMINI_API_KEY_HERE"
  },
  "ollama": {
    "api_url": "http://localhost:11434/api/generate",
    "model": "gemma3:4b"
  },
  "features": {
    "enable_enhancement": true,
    "enable_analytics": true,
    "enable_scheduling": true,
    "enable_multi_platform": true,
    "enable_hashtag_optimization": true
  }
}
```

## 📁 Output Structure

### Simple Mode

```
instagram_posts_[timestamp]/
└── Chronological_Posts/
    ├── 2024-01-15_Post_1/
    │   ├── 01_photo1.jpg
    │   ├── 02_photo2.jpg
    │   └── captions.txt
    └── 2024-01-16_Post_2/
```

### Advanced Mode (with optional features)

```
instagram_posts_[timestamp]/
├── Chronological_Posts/
├── Highlights_Posts/
├── analytics/
│   ├── report.txt
│   └── charts.png
└── posting_schedule.json
```

## 🛠️ Helper Scripts

### Setup and Migration

- **`setup_llama.py`** - Interactive setup for new Llama API users
- **`migrate_to_llama.py`** - Migrate existing Gemini/Ollama setup to Llama
- **`test_llama_api.py`** - Test Llama API integration with sample image

### Usage Examples

```bash
# First-time setup
python utils/setup_llama.py

# Migrate from Gemini/Ollama
python utils/migrate_to_llama.py

# Test API connection
python tests/test_llama_api.py
```

## 🖥️ Interactive Web Interface

Prefer a dashboard over the terminal? Launch the built-in web application to configure every command-line flag visually,
preview your source imagery, and start/stop processing with a single click.

```bash
pip install -r requirements.txt
python webui/server.py  # the server runs on http://localhost:8000 by default
```

**Highlights**

- Idle-by-default landing screen with live status indicator
- Form controls for **every** CLI argument (including toggles, selects, and numeric inputs)
- Start/Stop controls that execute the organizer using your selections
- Real-time log viewer that mirrors console output and supports clearing history
- Rich image gallery preview for the configured source directory (updates automatically when the path changes)

Once the server is running, open your browser to `http://localhost:8000` to begin.

## 🎯 Use Cases

### First Time Testing

```bash
python ai_instagram_organizer.py --ai-provider gemini --gemini-key YOUR_KEY --dev-mode --limit 5
```

### Travel Photos

```bash
python ai_instagram_organizer.py --source "~/Photos/Trip" --post-size 12
```

### Quick Processing

```bash
python ai_instagram_organizer.py --simple-mode --dev-mode --limit 50
```

## 🔧 Advanced Setup

### For Full Features (Optional)

```bash
# Install additional dependencies for advanced features
pip install matplotlib seaborn opencv-python

# Run with all features enabled
python ai_instagram_organizer.py --config config.json
```

### Custom AI Models

Edit `config.json`:

```json
{
  "ollama": {
    "model": "llava:13b"
  },
  "gemini": {
    "model": "gemini-1.5-pro"
  }
}
```

## 🐛 Troubleshooting

### Gemini Issues

- **"API key required"**: Add `--gemini-key YOUR_KEY`
- **"Invalid API key"**: Check your key at [Google AI Studio](https://aistudio.google.com/app/apikey)

### Ollama Issues

- **"Connection refused"**: Run `ollama serve` first
- **"Model not found"**: Run `ollama pull gemma3:4b`

### General Issues

- **"No Instagram-worthy photos"**: The AI is being selective - this is normal
- **"Source folder not found"**: Check your path is correct
- **Memory issues**: Use `--dev-mode --limit 10`

## 💡 Tips

1. **Start with Gemini**: Easier setup, faster results
2. **Test small first**: Always use `--dev-mode --limit 5` initially
3. **Use simple mode**: Add `--simple-mode` if you don't need advanced features
4. **Check your photos**: Make sure they're actual photos, not screenshots

## 📦 Dependencies

### Required

```bash
pip install pillow imagehash pillow-heif requests
```

### Optional (for advanced features)

```bash
pip install matplotlib seaborn opencv-python
```

## 🔄 Switching Between AI Providers

```bash
# Use Gemini (cloud-based, fast)
python ai_instagram_organizer.py --ai-provider gemini --gemini-key YOUR_KEY

# Use Ollama (local, private)
python ai_instagram_organizer.py --ai-provider ollama
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests! Some ideas for contributions:

- Additional social media platforms
- More sophisticated AI prompts
- Integration with social media APIs
- Advanced image filters and effects
- Batch processing optimizations

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🙏 Acknowledgments

- **Ollama** for providing local AI capabilities
- **LLaVA** for vision-language understanding
- **PIL/Pillow** for image processing
- The open-source community for inspiration and tools

---

**Happy posting! 📸✨**
