# FreeFlowTTS

A modular, open-source Text-to-Speech (TTS) framework with a focus on Urdu language support.

## Features
- **Modular Architecture**: Easily swappable TTS engines.
- **Urdu Support**: Uses Meta's MMS (Massively Multilingual Speech) model for high-quality Urdu synthesis.
- **English Support**: Uses Microsoft's SpeechT5 model.
- **ElevenLabs Integration**: Optional support for ElevenLabs API (requires API Key) for realistic multilingual synthesis.
- **API & UI**: Includes a FastAPI backend and a Streamlit frontend.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run the Web Interface
```bash
streamlit run app.py
```

### Run the API Server
```bash
uvicorn src.api.main:app --reload
```

## Evaluation

To assess speech naturalness and quality:
1.  **Subjective Evaluation (MOS)**: Conduct Mean Opinion Score tests where human listeners rate synthesized speech on a scale of 1-5.
2.  **Objective Metrics**:
    -   **RTF (Real-Time Factor)**: Measure generation time vs audio duration.
    -   **MCD (Mel Cepstral Distortion)**: Requires ground truth audio.

## Architecture

-   `src/core`: Base classes and Model Manager.
-   `src/engines`: Implementations of specific TTS models.
-   `src/api`: FastAPI application.
-   `src/text`: Text processing utilities.
