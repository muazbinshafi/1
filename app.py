import streamlit as st
import numpy as np
from src.core.model_manager import ModelManager
from src.engines.mms_engine import MMSEngine
from src.engines.speecht5_engine import SpeechT5Engine

st.set_page_config(page_title="FreeFlowTTS", page_icon="🗣️")

st.title("🗣️ FreeFlowTTS: Open-Source Multilingual TTS")
st.write("Generating high-quality speech from text using free open-source models.")

# Initialize ModelManager (cached to avoid reloading)
@st.cache_resource
def get_manager():
    manager = ModelManager()
    manager.register_engine("mms", MMSEngine)
    manager.register_engine("speecht5", SpeechT5Engine)
    return manager

manager = get_manager()

# Sidebar for controls
st.sidebar.header("Settings")
language = st.sidebar.selectbox("Select Language", ["English", "Urdu"])

default_text = "Hello, how are you?" if language == "English" else "السلام علیکم، آپ کیسے ہیں؟"
text_input = st.text_area("Enter Text", height=150, value=default_text)

if st.button("Synthesize"):
    if not text_input.strip():
        st.warning("Please enter some text.")
    else:
        with st.spinner("Generating speech..."):
            try:
                if language == "English":
                    engine = manager.get_engine("speecht5")
                    lang_code = "eng"
                else:
                    engine = manager.get_engine("mms")
                    lang_code = "urd"

                rate, audio = engine.synthesize(text_input, lang_code)

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
All models are open-source and run locally.
""")
