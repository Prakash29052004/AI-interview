import asyncio
import os
from edge_tts import Communicate

async def text_to_speech(text: str, output_path: str) -> None:
    try:
        print(f"Starting TTS for text: {text[:50]}...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create communicate object
        communicate = Communicate(text, "en-US-AriaNeural")
        
        # Save audio file
        await communicate.save(output_path)
        
        print(f"TTS completed successfully: {output_path}")
        
    except Exception as e:
        print(f"TTS error: {e}")
        # Try with a different voice if the first one fails
        try:
            print("Trying alternative voice...")
            communicate = Communicate(text, "en-US-JennyNeural")
            await communicate.save(output_path)
            print(f"TTS completed with alternative voice: {output_path}")
        except Exception as e2:
            print(f"TTS failed with alternative voice: {e2}")
            raise Exception(f"TTS failed: {str(e2)}") 