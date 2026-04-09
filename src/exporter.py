from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from .ledger_store import LedgerStore


def export_month_excel(store: LedgerStore, month_yyyy_mm: str, export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_dir / f"ledger_{month_yyyy_mm.replace('-', '_')}.xlsx"

    rows = store.fetch_month(month_yyyy_mm)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "transactions"
    sheet.append(["date", "transaction_amount", "category", "extra_tags"])
    for row in rows:
        sheet.append(list(row))
    workbook.save(output_path)

    return output_path
