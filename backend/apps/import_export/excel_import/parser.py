"""Parsing helpers for target Excel workbook."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .constants import DATA_SHEET_NAME, REQUIRED_COLUMNS
from .normalizers import is_blank, normalize_header


@dataclass
class ParsedWorkbook:
    rows: list[tuple[int, dict[str, Any]]]
    errors: list[dict[str, Any]]


def _is_numbering_row(row: dict[str, Any]) -> bool:
    values = [v for v in row.values() if not is_blank(v)]
    if len(values) < 3:
        return False

    numeric = []
    for value in values[:21]:
        text = str(value).strip()
        if not text.isdigit():
            return False
        numeric.append(int(text))

    if not numeric:
        return False

    return numeric == list(range(1, len(numeric) + 1))


def parse_excel(path: str) -> ParsedWorkbook:
    errors: list[dict[str, Any]] = []
    try:
        try:
            df = pd.read_excel(path, sheet_name=DATA_SHEET_NAME, dtype=object)
        except ValueError:
            df = pd.read_excel(path, dtype=object)
    except Exception as exc:
        return ParsedWorkbook(rows=[], errors=[{"row": 0, "message": f"Не удалось прочитать файл: {exc}"}])

    df.columns = [normalize_header(c) for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        errors.append({
            "row": 0,
            "message": f"Отсутствуют обязательные колонки: {', '.join(sorted(missing))}",
        })
        return ParsedWorkbook(rows=[], errors=errors)

    rows: list[tuple[int, dict[str, Any]]] = []
    for idx, row in df.iterrows():
        row_num = idx + 2
        row_dict = {col: row.get(col) for col in df.columns}
        if _is_numbering_row(row_dict):
            continue
        rows.append((row_num, row_dict))

    return ParsedWorkbook(rows=rows, errors=errors)
