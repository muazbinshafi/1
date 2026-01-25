from typing import Dict, Type
from src.core.interface import TTSEngine

class ModelManager:
    """
    Manages multiple TTS engines.
    """
    def __init__(self):
        self._engines: Dict[str, TTSEngine] = {}
        self._engine_classes: Dict[str, Type[TTSEngine]] = {}

    def register_engine(self, name: str, engine_class: Type[TTSEngine]):
        """
        Registers an engine class.
        """
        self._engine_classes[name] = engine_class

    def load_engine(self, name: str) -> TTSEngine:
        """
        Loads and returns an engine instance.
        """
        if name in self._engines:
            return self._engines[name]

        if name not in self._engine_classes:
            raise ValueError(f"Engine '{name}' is not registered.")

        engine_instance = self._engine_classes[name]()
        print(f"Loading engine: {name}...")
        engine_instance.load()
        self._engines[name] = engine_instance
        print(f"Engine {name} loaded.")
        return engine_instance

    def get_engine(self, name: str) -> TTSEngine:
        """
        Returns an already loaded engine.
        """
        if name not in self._engines:
             return self.load_engine(name)
        return self._engines[name]

    def list_engines(self) -> list[str]:
        return list(self._engine_classes.keys())
