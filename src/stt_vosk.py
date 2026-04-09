from __future__ import annotations

import json
from pathlib import Path

from vosk import KaldiRecognizer, Model


class VoskEngine:
    def __init__(self, model_path: Path, sample_rate: int):
        if not model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at '{model_path}'. Download a model and place it in this path."
            )
        self.model = Model(str(model_path))
        self.recognizer = KaldiRecognizer(self.model, sample_rate)

    def accept_audio(self, audio_bytes: bytes) -> str | None:
        if self.recognizer.AcceptWaveform(audio_bytes):
            data = json.loads(self.recognizer.Result())
            text = data.get("text", "").strip()
            return text or None
        return None
