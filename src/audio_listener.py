from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable

import sounddevice as sd

from .config import BLOCKSIZE, CHANNELS, SAMPLE_RATE
from .stt_vosk import VoskEngine


class AudioListener:
    def __init__(self, stt_engine: VoskEngine, on_text: Callable[[str], None]):
        self.stt_engine = stt_engine
        self.on_text = on_text
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="audio-listener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _audio_callback(self, indata, _frames, _time, status) -> None:
        if status:
            logging.warning("Audio status: %s", status)
        self._audio_queue.put(bytes(indata))

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                with sd.RawInputStream(
                    samplerate=SAMPLE_RATE,
                    blocksize=BLOCKSIZE,
                    device=None,
                    dtype="int16",
                    channels=CHANNELS,
                    callback=self._audio_callback,
                ):
                    logging.info("Microphone listener started.")
                    while not self._stop_event.is_set():
                        audio_bytes = self._audio_queue.get(timeout=1.0)
                        text = self.stt_engine.accept_audio(audio_bytes)
                        if text:
                            logging.info("Recognized text: %s", text)
                            self.on_text(text)
            except queue.Empty:
                continue
            except Exception:
                logging.exception("Audio listener failed; retrying in loop.")
