from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from .audio_listener import AudioListener
from .config import DB_PATH, EXPORT_DIR, PAUSE_JOIN_SECONDS, VOSK_MODEL_DIR
from .exporter import export_month_excel
from .ledger_store import LedgerStore
from .stt_vosk import VoskEngine
from .transaction_parser import has_transaction_intent, parse_transactions


def _build_icon() -> Image.Image:
    img = Image.new("RGB", (64, 64), color=(28, 117, 188))
    draw = ImageDraw.Draw(img)
    draw.rectangle((18, 12, 46, 52), fill=(255, 255, 255))
    draw.rectangle((22, 16, 42, 22), fill=(28, 117, 188))
    draw.line((22, 30, 42, 30), fill=(28, 117, 188), width=2)
    draw.line((22, 36, 42, 36), fill=(28, 117, 188), width=2)
    return img


class TrayVoiceLedgerApp:
    def __init__(self):
        self.store = LedgerStore(DB_PATH)
        self.stt = VoskEngine(VOSK_MODEL_DIR, sample_rate=16_000)
        self.listener = AudioListener(self.stt, on_text=self._handle_recognized_text)
        self.icon: pystray.Icon | None = None
        self._pending_text = ""
        self._pending_time = 0.0

    def _handle_recognized_text(self, text: str) -> None:
        if not has_transaction_intent(text):
            return
        logging.info("Transaction-intent transcript: %s", text)

        now = time.time()
        if self._pending_text and (now - self._pending_time) <= PAUSE_JOIN_SECONDS:
            candidate_text = f"{self._pending_text} {text}".strip()
        else:
            candidate_text = text.strip()

        parsed_transactions = parse_transactions(candidate_text)
        if not parsed_transactions:
            # Keep candidate briefly so a follow-up chunk after a short pause can complete it.
            self._pending_text = candidate_text
            self._pending_time = now
            logging.warning("Unable to parse candidate transaction text: %s", candidate_text)
            return

        for parsed in parsed_transactions:
            self.store.add_transaction(parsed)
            logging.info("Saved transaction: %s", parsed)
        self._pending_text = ""
        self._pending_time = 0.0

    def _prompt_month(self) -> str | None:
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        month = simpledialog.askstring("Export Monthly Excel", "Enter month (YYYY-MM):")
        root.destroy()
        if not month:
            return None
        month = month.strip()
        if len(month) != 7 or month[4] != "-":
            return None
        return month

    def _on_export(self, icon, item) -> None:
        del item
        month = self._prompt_month()
        if not month:
            icon.notify("Invalid month. Use YYYY-MM.", "Voice Ledger")
            return

        path = export_month_excel(self.store, month, EXPORT_DIR)
        icon.notify(f"Exported: {Path(path).name}", "Voice Ledger")

    def _on_exit(self, icon, item) -> None:
        del item
        self.listener.stop()
        icon.stop()

    def run(self) -> None:
        self.listener.start()
        menu = pystray.Menu(
            pystray.MenuItem("Export Monthly Excel", self._on_export),
            pystray.MenuItem("Exit", self._on_exit),
        )
        self.icon = pystray.Icon("voice-ledger", _build_icon(), "Voice Ledger", menu)
        self.icon.run()


def run_app_in_thread() -> threading.Thread:
    app = TrayVoiceLedgerApp()
    thread = threading.Thread(target=app.run, daemon=False, name="tray-main")
    thread.start()
    return thread
