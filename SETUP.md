# Local Development Setup

## Environment Variables Setup

### Method 1: Create .env File (Recommended)

1. Create a `.env` file in the project root:
```bash
touch .env
```

2. Add your API keys to the `.env` file:
```env
# OpenRouter API Configuration
# Get your API key from: https://openrouter.ai/settings/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Flask Configuration
FLASK_ENV=development
PORT=8080

# Optional: Hugging Face API Token (for speech analysis)
HF_API_TOKEN=your_huggingface_token_here
```

### Method 2: Set Environment Variable in Terminal

**macOS/Linux:**
```bash
export OPENROUTER_API_KEY="your_api_key_here"
python app.py
```

**Windows Command Prompt:**
```cmd
set OPENROUTER_API_KEY=your_api_key_here
python app.py
```

**Windows PowerShell:**
```powershell
$env:OPENROUTER_API_KEY="your_api_key_here"
python app.py
```

### Method 3: Use a Shell Script

Create a `run.sh` file:
```bash
#!/bin/bash
export OPENROUTER_API_KEY="your_api_key_here"
export FLASK_ENV=development
python app.py
```

Make it executable and run:
```bash
chmod +x run.sh
./run.sh
```

## Getting Your OpenRouter API Key

1. Go to https://openrouter.ai/settings/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key and add it to your environment

## Testing the Setup

After setting up your API key, you can test it by:

1. Starting the app: `python app.py`
2. Opening http://localhost:8080
3. Going to the "DeepSeek Chatbot" tab
4. You should see "✅ API Connected" if the key is working

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Keep your API keys secure and don't share them 