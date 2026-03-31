"""Public import service entrypoint (kept stable for callers/tests)."""
from __future__ import annotations

from .excel_import import ImportResult, RowError, process_import_log
from .models import ImportLog


def process_excel_import(import_log: ImportLog) -> None:
    process_import_log(import_log)


__all__ = ["process_excel_import", "ImportResult", "RowError"]
