import os
import sys
import soundfile as sf
sys.path.append(os.getcwd())
from src.engines.elevenlabs_engine import ElevenLabsEngine

def test_elevenlabs():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Skipping ElevenLabs test: No API Key provided.")
        return

    engine = ElevenLabsEngine()
    # The engine init reads env var too, but let's ensure it's working.

    print("Synthesizing Urdu text via ElevenLabs...")
    text = "یہ ایک ٹیسٹ ہے۔"
    try:
        rate, audio = engine.synthesize(text, "urd")
        sf.write("test_elevenlabs_urdu.wav", audio, rate)
        print("Success! Saved test_elevenlabs_urdu.wav")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_elevenlabs()
