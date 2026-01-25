from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import numpy as np
from src.core.interface import TTSEngine

class SpeechT5Engine(TTSEngine):
    def __init__(self):
        self.model_id = "microsoft/speecht5_tts"
        self.vocoder_id = "microsoft/speecht5_hifigan"
        self.processor = None
        self.model = None
        self.vocoder = None
        self.speaker_embeddings = None

    def load(self):
        print("Loading SpeechT5 model...")
        self.processor = SpeechT5Processor.from_pretrained(self.model_id)
        self.model = SpeechT5ForTextToSpeech.from_pretrained(self.model_id)
        self.vocoder = SpeechT5HifiGan.from_pretrained(self.vocoder_id)

        # Load default speaker embedding
        # Ideally we would cache this or have it locally, but we'll fetch from HF datasets
        print("Loading speaker embeddings...")
        embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation", trust_remote_code=True)
        self.speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)
        print("SpeechT5 loaded.")

    def synthesize(self, text: str, language: str = None, **kwargs) -> tuple[int, np.ndarray]:
        if not self.model:
            self.load()

        inputs = self.processor(text=text, return_tensors="pt")

        with torch.no_grad():
            speech = self.model.generate_speech(inputs["input_ids"], self.speaker_embeddings, vocoder=self.vocoder)

        return 16000, speech.numpy()

    @property
    def name(self) -> str:
        return "SpeechT5-English"

    @property
    def supported_languages(self) -> list[str]:
        return ["eng"]
