"""
Shared Excel import-template generator.

Single source of truth for the sample rows / column order used by:
  * ``pc_import_template`` view  (browser download button)
  * ``create_sample_excel`` management command

Usage::

    from apps.inventory.services.template_excel import build_import_template_bytes
    excel_bytes = build_import_template_bytes()

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

import io

import pandas as pd

# Column order must match what process_excel_import() expects.
COLUMNS: list[str] = [
    "name", "inventory_number", "device_type",
    "cpu", "ram", "storage_type", "storage_size",
    "os", "status", "location", "assigned_to",
]

# Two example rows that show the expected values for each field.
SAMPLE_ROWS: list[dict] = [
    {
        "name":             "ПК-001",
        "inventory_number": "INV-2024-001",
        "device_type":      "PC",
        "cpu":              "Intel Core i5-12400",
        "ram":              16,
        "storage_type":     "SSD",
        "storage_size":     512,
        "os":               "Windows 11 Pro",
        "status":           "active",
        "location":         "Главный офис",
        "assigned_to":      "ivanov",
    },
    {
        "name":             "ПК-002",
        "inventory_number": "INV-2024-002",
        "device_type":      "PC",
        "cpu":              "AMD Ryzen 5 5600",
        "ram":              8,
        "storage_type":     "HDD",
        "storage_size":     1000,
        "os":               "Windows 10 Pro",
        "status":           "broken",
        "location":         "Филиал №1",
        "assigned_to":      "",
    },
]

# Column widths (characters) matching COLUMNS order.
_COL_WIDTHS: list[int] = [20, 20, 12, 25, 6, 13, 14, 20, 10, 20, 15]


def build_import_template_bytes() -> bytes:
    """
    Build the Excel import template and return its raw bytes.

    The returned bytes can be:
    * Streamed directly in an ``HttpResponse`` for browser download.
    * Written to a file with ``Path.write_bytes()``.
    """
    df = pd.DataFrame(SAMPLE_ROWS, columns=COLUMNS)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Импорт")
        ws = writer.sheets["Импорт"]
        for col_idx, width in enumerate(_COL_WIDTHS, start=1):
            col_letter = ws.cell(row=1, column=col_idx).column_letter
            ws.column_dimensions[col_letter].width = width

    return buf.getvalue()
