# AI Interview System

A real-time audio interview system with AI-powered transcription and response generation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Gemini AI API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Getting Your Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Use it in your `.env` file or environment variable

### Installation

1. **Setup virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Gemini AI API key:**

   **Option A: Using .env file (Recommended)**
   ```bash
   # Create a .env file in the project root
   echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
   ```
   
   **Option B: Environment variable**
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_gemini_api_key_here
   
   # Linux/Mac
   export GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Start the backend:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. **Start the frontend:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 🎯 Features

- **Real-time audio recording** with browser-based interface
- **Automatic speech-to-text transcription** using Whisper
- **AI-powered entity extraction and FAQ generation** using Gemini AI
- **Text-to-speech response generation** using Edge TTS
- **Sample audio testing** with pre-recorded interview examples
- **HR confirmation system** with review before submission
- **Database logging** of all interactions
- **Error handling and recovery** for robust operation

## 🔧 Troubleshooting

### Backend Connection Issues

**Problem**: "Cannot connect to backend" or "Connection timeout"

**Solutions**:
1. Make sure the backend is running:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. Check if port 8000 is available:
   ```bash
   netstat -an | findstr :8000  # Windows
   lsof -i :8000  # Linux/Mac
   ```

3. Try the test endpoint:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

### Audio Processing Issues

**Problem**: "Processing only, no output showing"

**Solutions**:
1. Check backend logs for errors
2. Ensure audio file is valid (.wav or .webm)
3. Try with a shorter audio file first
4. Check if all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

### Gemini AI Issues

**Problem**: "Failed to get an answer from the AI model" or "API key not found"

**Solutions**:
1. Ensure your Gemini API key is set correctly:
   ```bash
   echo $GOOGLE_API_KEY  # Linux/Mac
   echo %GOOGLE_API_KEY% # Windows
   ```

2. Verify your API key is valid by testing it:
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_API_KEY"
   ```

3. Check if you have sufficient quota/credits in your Google AI Studio account

## 📁 Project Structure

```
AI-Interview/
├── app/
│   ├── main.py          # FastAPI backend
│   ├── audio_utils.py   # Audio transcription
│   ├── nlp.py          # Entity extraction
│   ├── faq.py          # FAQ matching
│   ├── tts.py          # Text-to-speech
│   ├── db.py           # Database operations
│   └── models.py       # Data models
├── streamlit_app.py    # Frontend interface
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## 🎮 Usage

1. **Start both services** (backend + frontend)
2. **Test connection** using the "Test Backend Connection" button
3. **Choose audio input method**:
   - **Record Audio**: Use browser recorder for live interviews
   - **Upload File**: Upload existing audio files (.wav or .webm)
   - **Test with Sample Audio**: Try pre-recorded sample interviews
4. **Review results** - transcription, entities, and AI response
5. **Confirm or reject** the response before sending to HR

### 🎧 Sample Audio Testing

The system includes several pre-recorded sample interviews for testing:
- **Ananya**: Technical candidate discussing Python, React, and 3 years experience
- **Prakash**: Developer discussing JavaScript, Node.js, and 2 years experience  
- **Govardhan**: Senior developer with extensive experience in full-stack development

Use these samples to test the system without recording your own audio.

## 🔍 Debug Mode

The backend now includes comprehensive logging. Check the console output for:
- File upload status
- Transcription progress
- Entity extraction results
- TTS generation status
- Database operations

## ⚡ Performance Optimizations

The backend includes several optimizations for faster startup and processing:
- **Preloaded Whisper Model**: Model is loaded once on startup, not per request
- **Warning Suppression**: Deprecation warnings are suppressed for cleaner output
- **Global Model Instance**: Reuses the same model instance across requests
- **Startup Messages**: Clear indication of backend startup progress

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review backend console logs
3. Try the test endpoints
4. Ensure all dependencies are installed correctly 