from __future__ import annotations

import logging

from .config import LOG_DIR
from .tray_app import TrayVoiceLedgerApp


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_DIR / "app.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def main() -> None:
    configure_logging()
    app = TrayVoiceLedgerApp()
    app.run()


if __name__ == "__main__":
    main()
