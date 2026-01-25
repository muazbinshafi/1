import requests
import numpy as np
import io
import soundfile as sf
import os
from src.core.interface import TTSEngine

class ElevenLabsEngine(TTSEngine):
    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel
        self.model_id = "eleven_multilingual_v2"
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"

    def load(self):
        # API-based, nothing to load into memory
        pass

    def synthesize(self, text: str, language: str = None, **kwargs) -> tuple[int, np.ndarray]:
        # Prefer kwargs key, then instance key, then env var
        api_key = kwargs.get("api_key", self.api_key)

        if not api_key:
            raise ValueError("ElevenLabs API Key is missing. Please provide it via kwargs or ELEVENLABS_API_KEY environment variable.")

        # Request PCM 24kHz
        url = f"{self.base_url}/{self.voice_id}?output_format=pcm_24000"

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
             raise RuntimeError(f"ElevenLabs API Error: {response.status_code} - {response.text}")

        # Read raw PCM 16-bit signed integer
        audio_data = np.frombuffer(response.content, dtype=np.int16)

        # Convert to float32 for consistency with other engines [-1.0, 1.0]
        audio_float = audio_data.astype(np.float32) / 32768.0

        return 24000, audio_float

    @property
    def name(self) -> str:
        return "ElevenLabs"

    @property
    def supported_languages(self) -> list[str]:
        # Multilingual v2 supports many languages including Urdu
        return ["urd", "eng", "hin", "ara", "ger", "pol", "spa", "ita", "fre", "por"]
