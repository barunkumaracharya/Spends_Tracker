from __future__ import annotations

import sqlite3
from pathlib import Path

from .transaction_parser import ParsedTransaction


class LedgerStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    date TEXT NOT NULL,
                    transaction_amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    extra_tags TEXT NOT NULL
                )
                """
            )

    def add_transaction(self, tx: ParsedTransaction) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO transactions (date, transaction_amount, category, extra_tags)
                VALUES (?, ?, ?, ?)
                """,
                (tx.date, tx.transaction_amount, tx.category, tx.extra_tags),
            )

    def fetch_month(self, month_yyyy_mm: str) -> list[tuple[str, float, str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT date, transaction_amount, category, extra_tags
                FROM transactions
                WHERE substr(date, 1, 7) = ?
                ORDER BY date ASC
                """,
                (month_yyyy_mm,),
            ).fetchall()
        return rows
