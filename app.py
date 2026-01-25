import streamlit as st
import numpy as np
import os
from src.core.model_manager import ModelManager
from src.engines.mms_engine import MMSEngine
from src.engines.speecht5_engine import SpeechT5Engine
from src.engines.elevenlabs_engine import ElevenLabsEngine

st.set_page_config(page_title="FreeFlowTTS", page_icon="🗣️")

st.title("🗣️ FreeFlowTTS: Open-Source Multilingual TTS")
st.write("Generating high-quality speech from text using free open-source models (and optional APIs).")

# Initialize ModelManager (cached to avoid reloading)
@st.cache_resource
def get_manager():
    manager = ModelManager()
    manager.register_engine("mms", MMSEngine)
    manager.register_engine("speecht5", SpeechT5Engine)
    manager.register_engine("elevenlabs", ElevenLabsEngine)
    return manager

manager = get_manager()

# Sidebar for controls
st.sidebar.header("Settings")
language = st.sidebar.selectbox("Select Language", ["English", "Urdu"])

# Engine selection logic
engine_options = []
if language == "English":
    engine_options = ["SpeechT5", "ElevenLabs"]
else: # Urdu
    engine_options = ["MMS", "ElevenLabs"]

selected_engine_name = st.sidebar.selectbox("Select Engine", engine_options)

api_key = None
if selected_engine_name == "ElevenLabs":
    api_key = st.sidebar.text_input("ElevenLabs API Key", type="password", help="Enter your ElevenLabs API Key here.")
    if not api_key:
         st.sidebar.warning("API Key required for ElevenLabs.")

default_text = "Hello, how are you?" if language == "English" else "السلام علیکم، آپ کیسے ہیں؟"
text_input = st.text_area("Enter Text", height=150, value=default_text)

if st.button("Synthesize"):
    if not text_input.strip():
        st.warning("Please enter some text.")
    elif selected_engine_name == "ElevenLabs" and not api_key:
        st.error("Please provide an ElevenLabs API Key.")
    else:
        with st.spinner("Generating speech..."):
            try:
                engine_key = ""
                lang_code = ""

                if selected_engine_name == "SpeechT5":
                    engine_key = "speecht5"
                    lang_code = "eng"
                elif selected_engine_name == "MMS":
                    engine_key = "mms"
                    lang_code = "urd"
                elif selected_engine_name == "ElevenLabs":
                    engine_key = "elevenlabs"
                    lang_code = "urd" if language == "Urdu" else "eng"

                engine = manager.get_engine(engine_key)

                # Pass api_key in kwargs. Other engines will ignore it.
                rate, audio = engine.synthesize(text_input, lang_code, api_key=api_key)

                st.audio(audio, sample_rate=rate)
                st.success("Speech generated successfully!")

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())

st.markdown("---")
st.markdown("### About")
st.markdown("""
This tool uses:
- **MMS (Meta)** for Urdu synthesis.
- **SpeechT5 (Microsoft)** for English synthesis.
- **ElevenLabs** (Optional) for realistic multilingual synthesis.
""")
