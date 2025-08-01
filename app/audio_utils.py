# Suppress warnings BEFORE any other imports
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

from faster_whisper import WhisperModel
import os
import tempfile
import shutil

# Global model instance to avoid reloading
_whisper_model = None

def get_whisper_model():
    """Get or create the global Whisper model instance"""
    global _whisper_model
    if _whisper_model is None:
        print("[AUDIO_UTILS] Loading Whisper model (this may take a moment on first run)...")
        _whisper_model = WhisperModel('small', device='cpu', compute_type='int8')
        print("[AUDIO_UTILS] Whisper model loaded successfully")
    return _whisper_model

def transcribe_audio(file_path: str) -> str:
    try:
        print(f"[AUDIO_UTILS] Starting transcription for: {file_path}")
        
        # Get the global model instance
        model = get_whisper_model()
        
        # Try to transcribe directly first
        try:
            print("[AUDIO_UTILS] Attempting direct transcription...")
            segments, info = model.transcribe(file_path)
            transcription = " ".join([segment.text for segment in segments])
            result = transcription.strip()
            print(f"[AUDIO_UTILS] Direct transcription successful: {result}")
            return result
        except Exception as e:
            print(f"[AUDIO_UTILS] Direct transcription failed: {e}")
            
            # Try with different parameters
            try:
                print("[AUDIO_UTILS] Attempting transcription with language specification...")
                segments, info = model.transcribe(file_path, language='en')
                transcription = " ".join([segment.text for segment in segments])
                result = transcription.strip()
                print(f"[AUDIO_UTILS] Language-specific transcription successful: {result}")
                return result
            except Exception as e2:
                print(f"[AUDIO_UTILS] Language-specific transcription failed: {e2}")
                
                # Try with different model settings
                try:
                    print("[AUDIO_UTILS] Attempting transcription with different settings...")
                    segments, info = model.transcribe(file_path, beam_size=5)
                    transcription = " ".join([segment.text for segment in segments])
                    result = transcription.strip()
                    print(f"[AUDIO_UTILS] Alternative transcription successful: {result}")
                    return result
                except Exception as e3:
                    print(f"[AUDIO_UTILS] All transcription attempts failed: {e3}")
                    return "Audio transcription failed. Please try with a different audio file."
                
    except Exception as e:
        print(f"[AUDIO_UTILS] Transcription error: {e}")
        return "Audio transcription failed. Please try again." 