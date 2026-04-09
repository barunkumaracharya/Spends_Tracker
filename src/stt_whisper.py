from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import whisper


class WhisperEngine:
    """
    Speech-to-Text engine using OpenAI's Whisper model.
    
    Whisper is a robust offline speech recognition model that works much better
    with noisy audio and accented speech compared to Vosk.
    """

    def __init__(self, model_size: str = "base", language: str = "en", device: str = "cpu"):
        """
        Initialize Whisper engine.
        
        Args:
            model_size: Model size - "tiny", "base", "small", "medium", "large"
                       Larger models are more accurate but slower.
            language: Language code (e.g., "en" for English)
            device: "cpu" or "cuda" (GPU)
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        
        logging.info(f"Loading Whisper {model_size} model on {device}...")
        self.model = whisper.load_model(model_size, device=device)
        logging.info(f"Whisper model loaded successfully")
        
        # Buffer for accumulating audio chunks
        self._audio_buffer = np.array([], dtype=np.float32)
        self._sample_rate = 16000
        self._silence_threshold = 0.01  # Threshold for silence detection
        self._last_transcription = ""

    def accept_audio(self, audio_bytes: bytes) -> str | None:
        """
        Accept audio chunk and return transcription if speech detected.
        
        Args:
            audio_bytes: Raw audio bytes (int16, 16kHz, mono)
            
        Returns:
            Transcribed text or None if no speech detected
        """
        # Convert bytes to float32 audio
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Accumulate audio
        self._audio_buffer = np.concatenate([self._audio_buffer, audio_np])
        
        # Check if we have enough audio for transcription (>2 seconds)
        if len(self._audio_buffer) < self._sample_rate * 2:
            return None
        
        # Check if audio contains silence (pause detected)
        rms = np.sqrt(np.mean(audio_np ** 2))
        if rms < self._silence_threshold and len(self._audio_buffer) > self._sample_rate * 0.5:
            # Transcribe accumulated audio
            result = self._transcribe_buffer()
            return result
        
        return None

    def _transcribe_buffer(self) -> str | None:
        """Transcribe buffered audio and return text."""
        if len(self._audio_buffer) < self._sample_rate * 0.5:  # Less than 0.5 seconds
            self._audio_buffer = np.array([], dtype=np.float32)
            return None
        
        try:
            # Transcribe using Whisper
            result = self.model.transcribe(
                self._audio_buffer,
                language=self.language,
                fp16=False,  # Set to True if using GPU for faster processing
            )
            text = result["text"].strip()
            
            # Clear buffer
            self._audio_buffer = np.array([], dtype=np.float32)
            
            if text and text != self._last_transcription:
                self._last_transcription = text
                return text
            
            return None
        except Exception as e:
            logging.error(f"Whisper transcription error: {e}")
            self._audio_buffer = np.array([], dtype=np.float32)
            return None

    def reset(self) -> None:
        """Reset audio buffer."""
        self._audio_buffer = np.array([], dtype=np.float32)
