# 🦙 Llama API Integration Guide

This guide covers the Llama API integration for the Instagram Photo Organizer, which is now the default AI provider.

## 🚀 Quick Setup

### 1. Get Your API Key

1. Visit [Llama API](https://api.llama.com)
2. Sign up for an account
3. Generate your API key from the dashboard

### 2. Configure the Tool

**Option A: Use the setup script (Recommended)**

```bash
python setup_llama.py
```

**Option B: Manual setup**

```bash
# Set environment variable
export LLAMA_API_KEY="your-api-key-here"

# Or update config.json directly
```

### 3. Test the Integration

```bash
# Run the test script
python test_llama_api.py

# Or run a quick test with the main tool
python ai_instagram_organizer.py --dev-mode --limit 5
```

## 🔧 Configuration

### Environment Variable

The tool looks for the API key in this order:

1. `--llama-key` command line argument
2. `LLAMA_API_KEY` environment variable
3. `api_key` in the config.json file

### Config File Settings

```json
{
  "ai_provider": "llama",
  "llama": {
    "api_key": "your-api-key-here",
    "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
    "api_url": "https://api.llama.com/v1/chat/completions",
    "timeout": 120
  }
}
```

## 🎯 Usage Examples

### Basic Usage

```bash
# Use default Llama provider
python ai_instagram_organizer.py --source "/path/to/photos"

# Specify Llama explicitly
python ai_instagram_organizer.py --ai-provider llama --source "/path/to/photos"

# With API key override
python ai_instagram_organizer.py --llama-key "your-key" --source "/path/to/photos"
```

### Development Mode

```bash
# Test with 5 photos
python ai_instagram_organizer.py --dev-mode --limit 5

# Test with specific folder
python ai_instagram_organizer.py --dev-mode --limit 10 --source "/path/to/test/photos"
```

## 🔍 Features

### Image Analysis

The Llama API provides:

- **Technical Quality Scoring**: Evaluates image sharpness, exposure, composition
- **Visual Appeal Assessment**: Rates aesthetic qualities and visual impact
- **Engagement Prediction**: Estimates potential Instagram engagement
- **Content Categorization**: Classifies images by type (portrait, landscape, etc.)
- **Mood Detection**: Identifies the emotional tone of images
- **Contextual Understanding**: Analyzes setting, lighting, and scene elements

### Content Generation

- **Smart Captions**: Generates 3 different caption options per post
- **Hashtag Optimization**: Creates relevant hashtags based on image content
- **Theme Detection**: Identifies overall post themes for consistency

## 🚨 Troubleshooting

### Common Issues

**API Key Not Found**

```
❌ Llama API key not provided. Set LLAMA_API_KEY environment variable or update config.
```

**Solution**: Set the environment variable or use the setup script

**Network/API Errors**

```
❌ Llama analysis error: HTTPSConnectionPool...
```

**Solution**: Check your internet connection and API key validity

**JSON Parsing Errors**

```
❌ Failed to parse Llama JSON response
```

**Solution**: This is usually temporary - the tool will retry automatically

### Debug Mode

Enable debug logging to see detailed API responses:

```bash
# Add debug logging (modify the script temporarily)
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 💡 Tips for Best Results

1. **Image Quality**: Higher quality images get better analysis results
2. **Batch Processing**: The tool handles rate limiting automatically
3. **Caching**: Analysis results are cached to avoid re-processing
4. **Fallback**: Keep Gemini or Ollama configured as backup options

## 🔄 Switching Between Providers

You can easily switch between AI providers:

```bash
# Use Llama (default)
python ai_instagram_organizer.py --ai-provider llama

# Use Gemini
python ai_instagram_organizer.py --ai-provider gemini --gemini-key YOUR_KEY

# Use Ollama (local)
python ai_instagram_organizer.py --ai-provider ollama
```

## 📊 Performance Comparison

| Provider | Speed | Quality | Cost | Setup |
|----------|-------|---------|------|-------|
| **Llama** | Fast | High | Pay-per-use | Easy |
| Gemini | Fast | High | Pay-per-use | Easy |
| Ollama | Medium | Good | Free | Complex |

## 🆘 Support

If you encounter issues:

1. Run the test script: `python test_llama_api.py`
2. Check the [Llama API documentation](https://api.llama.com/docs)
3. Verify your API key is valid and has sufficient credits
4. Try switching to Gemini as a fallback option

## 🔐 Security Notes

- Never commit API keys to version control
- Use environment variables for production deployments
- Rotate API keys regularly
- Monitor your API usage and costs
