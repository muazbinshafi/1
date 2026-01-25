from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
from src.core.interface import TTSEngine
from src.text.urdu_normalizer import UrduNormalizer

class MMSEngine(TTSEngine):
    def __init__(self):
        self.model_id = "facebook/mms-tts-urd-script_arabic"
        self.model = None
        self.tokenizer = None
        self.normalizer = UrduNormalizer()

    def load(self):
        print(f"Loading MMS model from {self.model_id}...")
        self.model = VitsModel.from_pretrained(self.model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        print("MMS model loaded.")

    def synthesize(self, text: str, language: str = None, **kwargs) -> tuple[int, np.ndarray]:
        if not self.model:
            self.load()

        # Normalize text
        text = self.normalizer.normalize(text)

        inputs = self.tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            output = self.model(**inputs).waveform

        # Convert to numpy and squeeze dimensions
        output_np = output.cpu().numpy().squeeze()

        return self.model.config.sampling_rate, output_np

    @property
    def name(self) -> str:
        return "MMS-Urdu"

    @property
    def supported_languages(self) -> list[str]:
        return ["urd"]
