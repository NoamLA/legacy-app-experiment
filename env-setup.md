# Environment Setup Guide

This guide helps you configure the environment variables for the Legacy Interview App.

## Quick Setup

1. **Copy the template file:**
   ```bash
   cp .env.template .env
   ```

2. **Edit the `.env` file** and add your API keys:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Required: Add your OpenAI API key:**
   ```
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   ```

## Required Configuration

### 🔑 OpenAI API Key
- **Where to get it**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Cost**: Pay-per-use (typically $0.01-0.03 per 1K tokens)
- **Required for**: All AI agents (question generation, theme identification, summarization)

### 🔐 Secret Key
Generate a secure secret key:
```bash
openssl rand -hex 32
```
Then add it to your `.env` file:
```
SECRET_KEY=your_generated_secret_key_here
```

## Optional Configuration

### 🎤 Voice Features
If you want to enable voice recording:
```
WHISPER_MODEL=base
MAX_AUDIO_SIZE_MB=25
```

### 🗄️ Database
For development, SQLite is fine (default):
```
DATABASE_URL=sqlite:///./legacy_interviews.db
```

For production, use PostgreSQL:
```
DATABASE_URL=postgresql://username:password@localhost:5432/legacy_interviews
```

### 📧 Email Notifications (Future)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Feature Flags

You can enable/disable features for testing:
```
FEATURE_VOICE_RECORDING=true
FEATURE_FAMILY_COLLABORATION=true
FEATURE_EXPORT_PODCAST=true
FEATURE_EXPORT_PDF=false
FEATURE_THEME_SUGGESTIONS=true
```

## Development vs Production

### Development Settings
```
NODE_ENV=development
DEBUG=true
LOG_API_REQUESTS=true
AGNO_LOG_LEVEL=INFO
```

### Production Settings
```
NODE_ENV=production
DEBUG=false
LOG_API_REQUESTS=false
AGNO_LOG_LEVEL=WARNING
```

## Environment Validation

The app will validate your environment on startup and show helpful error messages for missing required variables.

## Security Notes

- **Never commit `.env` to version control**
- **Use strong, unique secret keys**
- **Rotate API keys regularly**
- **Use environment-specific configurations**

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Check that `OPENAI_API_KEY` is set in `.env`
   - Ensure the key starts with `sk-`

2. **"Database connection failed"**
   - Verify `DATABASE_URL` format
   - Check database permissions

3. **"CORS errors in browser"**
   - Ensure `CORS_ORIGINS` includes your frontend URL
   - Check that ports match between frontend and backend

### Validation Script

Run this to check your environment:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['OPENAI_API_KEY', 'SECRET_KEY']
for key in required:
    if os.getenv(key):
        print(f'✅ {key}: Set')
    else:
        print(f'❌ {key}: Missing')
"
```

## Example Minimal .env

For quick testing, here's a minimal `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=your-secret-key-here
AGNO_TELEMETRY=false
DEBUG=true
```

---
**📅 Last Updated:** September 27, 2025
