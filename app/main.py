# Suppress warnings BEFORE any other imports
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from .audio_utils import transcribe_audio, get_whisper_model
from .nlp import extract_entities
from .tts import text_to_speech
from .db import get_db
from .models import InterviewLog
from sqlalchemy.orm import Session
import asyncio
import requests
import google.generativeai as genai

app = FastAPI()

# Initialize Gemini AI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Get the absolute path to the .env file (project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

print(f"🔍 Loading .env from: {env_path}")
print(f"📁 .env exists: {os.path.exists(env_path)}")

# Load .env file from the correct path
load_dotenv(env_path)

# Get API key from environment variable (handle BOM issue)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try with BOM character (Windows UTF-8 issue)
    api_key = os.getenv("\ufeffGOOGLE_API_KEY")
    if api_key:
        print(f"✅ Found API key with BOM: {api_key[:10]}...")
    else:
        print(f"❌ API key not found in environment")
        print(f"🔍 Available env vars: {[k for k in os.environ.keys() if 'GOOGLE' in k]}")
        raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in your .env file or environment.")

if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in your .env file or environment.")

print(f"✅ API key loaded: {api_key[:10]}...")
genai.configure(api_key=api_key)

# Preload Whisper model on startup to avoid delays during first transcription
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting AI Interview Backend...")
    print("📝 Preloading Whisper model for faster transcription...")
    get_whisper_model()  # This will load the model once on startup
    print("✅ Backend startup complete!")

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

UPLOAD_DIR = "uploads"
SAMPLE_AUDIO_DIR = "sample_audio"
AUDIO_RESP_DIR = "tts_responses"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAMPLE_AUDIO_DIR, exist_ok=True)
os.makedirs(AUDIO_RESP_DIR, exist_ok=True)

# Sample audio files for testing
SAMPLE_AUDIO_FILES = {
    "ananya": {
        "filename": "Ananya.wav",
        "description": "Ananya - Technical candidate discussing Python, React, and 3 years experience",
        "size": "1.5MB"
    },
    "prakash": {
        "filename": "Prakash.wav", 
        "description": "Prakash - Developer discussing JavaScript, Node.js, and 2 years experience",
        "size": "1.6MB"
    },
    "govardhan": {
        "filename": "Govardhan.wav",
        "description": "Govardhan - Senior developer with extensive experience in full-stack development",
        "size": "1.8MB"
    }
}

@app.get("/")
async def root():
    return {"message": "AI Interview Backend is running!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/sample-audio-files")
async def get_sample_audio_files():
    """Get list of available sample audio files for testing"""
    return {
        "sample_files": SAMPLE_AUDIO_FILES,
        "message": "Use these sample files to test the interview system"
    }

@app.get("/sample-audio/{sample_id}")
async def get_sample_audio(sample_id: str):
    """Serve a specific sample audio file"""
    if sample_id not in SAMPLE_AUDIO_FILES:
        raise HTTPException(status_code=404, detail="Sample audio file not found")
    
    filename = SAMPLE_AUDIO_FILES[sample_id]["filename"]
    file_path = os.path.join(SAMPLE_AUDIO_DIR, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Sample audio file not found on server")

@app.post("/test-sample-audio/{sample_id}")
async def test_sample_audio(sample_id: str, db: Session = Depends(get_db)):
    """Test the system with a specific sample audio file"""
    if sample_id not in SAMPLE_AUDIO_FILES:
        raise HTTPException(status_code=404, detail="Sample audio file not found")
    
    filename = SAMPLE_AUDIO_FILES[sample_id]["filename"]
    file_path = os.path.join(SAMPLE_AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample audio file not found on server")
    
    try:
        # Process the sample audio file
        transcription = transcribe_audio(file_path)
        if not transcription:
            raise HTTPException(status_code=500, detail="Transcription failed")

        # Extract entities and generate FAQs
        analysis_data = extract_entities(transcription)
        analysis_data['transcription'] = transcription
        analysis_data['sample_file_used'] = sample_id
        analysis_data['sample_description'] = SAMPLE_AUDIO_FILES[sample_id]["description"]

        # Log to DB
        try:
            log = InterviewLog(
                filename=f"sample_{sample_id}_{filename}",
                transcription=transcription,
                candidate_name=analysis_data.get("candidate_name"),
                years_experience=analysis_data.get("years_experience"),
                desired_role=analysis_data.get("desired_role")
            )
            log.set_skills(analysis_data.get("skills", []))
            log.set_selected_faq(analysis_data.get("faq", []))
            db.add(log)
            db.commit()
            db.refresh(log)
            analysis_data["session_id"] = log.id
        except Exception as db_error:
            print(f"Database error (non-critical): {db_error}")
            analysis_data["session_id"] = None
        
        return JSONResponse(content=analysis_data)
        
    except Exception as e:
        print(f"Error processing sample audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing sample audio: {str(e)}")

@app.post("/upload-audio-json/")
async def upload_audio_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Main endpoint to process audio. It performs transcription and gets entities 
    and dynamic FAQs from Ollama in a single step. No audio is generated here.
    """
    try:
        timestamp_base = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        filename = f"{timestamp_base}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        transcription = transcribe_audio(file_path)
        if not transcription:
            raise HTTPException(status_code=500, detail="Transcription failed")

        # Single call to get entities and dynamic FAQs text
        analysis_data = extract_entities(transcription)

        # Add the transcription to the response data so the frontend can access it
        analysis_data['transcription'] = transcription

        # Log to DB
        try:
            log = InterviewLog(
                filename=filename,
                transcription=transcription,
                candidate_name=analysis_data.get("candidate_name"),
                years_experience=analysis_data.get("years_experience"),
                desired_role=analysis_data.get("desired_role")
            )
            log.set_skills(analysis_data.get("skills", []))
            log.set_selected_faq(analysis_data.get("faq", []))
            db.add(log)
            db.commit()
            db.refresh(log)
            analysis_data["session_id"] = log.id
        except Exception as db_error:
            print(f"Database error (non-critical): {db_error}")
            analysis_data["session_id"] = None
        
        return JSONResponse(content=analysis_data)
        
    except Exception as e:
        print(f"Unexpected error in upload_audio_json: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/answer-manual-faq/")
async def answer_manual_faq(payload: dict = Body(...)):
    """
    Answers a manually entered question from HR based on the transcription.
    """
    transcription = payload.get("transcription")
    question = payload.get("question")
    if not transcription or not question:
        raise HTTPException(status_code=400, detail="Transcription and question are required.")

    prompt = (
        "You are an AI assistant. Based *only* on the provided transcript, answer the following question. "
        "Keep the answer concise and factual.\n\n"
        f"Transcript: \"{transcription}\"\n\n"
        f"Question: \"{question}\"\n\n"
        "Answer:"
    )

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        if response.text:
            answer = response.text.strip()
        else:
            answer = "Could not generate an answer from the transcript."
        
        return {"answer": answer}
    except Exception as e:
        print(f"Error calling Gemini for manual FAQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to get an answer from the AI model.")

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files"""
    file_path = os.path.join(AUDIO_RESP_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio file not found")

@app.post("/tts-for-faq/")
async def tts_for_faq(payload: dict = Body(...)):
    """
    Generates TTS for a selected FAQ's answer on-demand.
    """
    try:
        faq_object = payload.get("faq")
        if not faq_object or not isinstance(faq_object, dict):
            raise HTTPException(status_code=400, detail="Payload must contain a 'faq' object.")

        answer = faq_object.get("answer")
        if not answer:
            raise HTTPException(status_code=400, detail="FAQ object must contain an 'answer' key.")
            
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        tts_filename = f"tts_{timestamp}_faq.mp3"
        tts_path = os.path.join(AUDIO_RESP_DIR, tts_filename)
        
        await text_to_speech(answer, tts_path)
        
        return {"audio_url": f"/audio/{tts_filename}"}
    except Exception as e:
        print(f"Error in tts_for_faq: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate TTS audio.") 