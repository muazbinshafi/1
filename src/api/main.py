from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import soundfile as sf
import io
import numpy as np
from src.core.model_manager import ModelManager
from src.engines.mms_engine import MMSEngine
from src.engines.speecht5_engine import SpeechT5Engine

app = FastAPI(title="FreeFlowTTS API")

model_manager = ModelManager()
# Register engines
model_manager.register_engine("mms", MMSEngine)
model_manager.register_engine("speecht5", SpeechT5Engine)

class SynthesisRequest(BaseModel):
    text: str
    language: str = "eng" # 'eng' or 'urd'
    engine: str = None # Optional, if not provided, inferred from language

@app.get("/languages")
def get_languages():
    return {
        "supported_languages": {
            "urd": "Urdu (MMS)",
            "eng": "English (SpeechT5)"
        }
    }

@app.post("/synthesize")
def synthesize(request: SynthesisRequest):
    # Select engine based on language if not specified
    engine_name = request.engine
    if not engine_name:
        if request.language == "urd":
            engine_name = "mms"
        elif request.language == "eng":
            engine_name = "speecht5"
        else:
            raise HTTPException(status_code=400, detail="Unsupported language or engine not specified")

    try:
        engine = model_manager.get_engine(engine_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        sampling_rate, audio_array = engine.synthesize(request.text, request.language)

        # Convert numpy array to bytes (WAV)
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, sampling_rate, format='WAV')
        buffer.seek(0)

        return Response(content=buffer.read(), media_type="audio/wav")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")
