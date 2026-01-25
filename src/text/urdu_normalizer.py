import unicodedata
import re

class UrduNormalizer:
    def normalize(self, text: str) -> str:
        """
        Normalizes Urdu text.
        """
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text
