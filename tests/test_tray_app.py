from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tray_app import TrayVoiceLedgerApp
from src.transaction_parser import ParsedTransaction


class DummyStore:
    def __init__(self):
        self.saved = []

    def add_transaction(self, tx: ParsedTransaction) -> None:
        self.saved.append(tx)


class DummyParser:
    def parse_transactions(self, text: str, now: datetime | None = None):
        if "spent" in text.lower():
            return [ParsedTransaction(date="2026-04-09", transaction_amount=123.0, category="test", extra_tags="")]
        return []


def test_only_records_transactions_starting_with_hello():
    app = TrayVoiceLedgerApp.__new__(TrayVoiceLedgerApp)
    app.store = DummyStore()
    app.parser = DummyParser()
    app.icon = None
    app._pending_text = ""
    app._pending_time = 0.0

    app._handle_recognized_text("I spent 100 rupees on coffee")
    assert app.store.saved == []

    app._handle_recognized_text("hello I spent 100 rupees on coffee")
    assert len(app.store.saved) == 1
    assert app.store.saved[0].category == "test"

    app._pending_text = "hello I spent 100 rupees on coffee"
    app._pending_time = datetime.now().timestamp()
    app._handle_recognized_text("and then I spent 200 rupees on snacks")
    assert len(app.store.saved) == 2
