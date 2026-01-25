from abc import ABC, abstractmethod
import numpy as np

class TTSEngine(ABC):
    """
    Abstract Base Class for Text-to-Speech Engines.
    """

    @abstractmethod
    def load(self):
        """
        Loads the model and resources.
        """
        pass

    @abstractmethod
    def synthesize(self, text: str, language: str = None, **kwargs) -> tuple[int, np.ndarray]:
        """
        Synthesizes speech from text.

        Args:
            text (str): The input text to synthesize.
            language (str, optional): The language code (e.g., 'eng', 'urd').
            **kwargs: Additional arguments (e.g., api_key, speaker_id).

        Returns:
            tuple[int, np.ndarray]: A tuple containing the sampling rate and the audio waveform as a numpy array.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the engine.
        """
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> list[str]:
        """
        Returns a list of supported language codes.
        """
        pass
