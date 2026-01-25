import sys
import os
sys.path.append(os.getcwd())

import soundfile as sf
from src.core.model_manager import ModelManager
from src.engines.mms_engine import MMSEngine
from src.engines.speecht5_engine import SpeechT5Engine

def test_generation():
    manager = ModelManager()
    manager.register_engine("mms", MMSEngine)
    manager.register_engine("speecht5", SpeechT5Engine)

    # Test Urdu
    print("Testing Urdu Generation...")
    mms = manager.get_engine("mms")
    rate_ur, audio_ur = mms.synthesize("سلام، یہ ایک ٹیسٹ ہے۔", "urd")
    sf.write("test_urdu.wav", audio_ur, rate_ur)
    print("Urdu audio saved to test_urdu.wav")

    # Test English
    print("Testing English Generation...")
    t5 = manager.get_engine("speecht5")
    rate_en, audio_en = t5.synthesize("Hello, this is a test.", "eng")
    sf.write("test_english.wav", audio_en, rate_en)
    print("English audio saved to test_english.wav")

if __name__ == "__main__":
    test_generation()
