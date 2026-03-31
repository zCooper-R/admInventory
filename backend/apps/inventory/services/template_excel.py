"""Shared Excel import-template generator for the new target format."""

from __future__ import annotations

import io

from openpyxl import Workbook

COLUMNS: list[str] = [
    "№ п/п",
    "Наименование юридического лица",
    "Адрес организации",
    "Наименование ОС",
    "Инв. №",
    "Наименование процессора",
    "Тактовая частота",
    "Оперативная память",
    "Тип диска",
    "Емкость диска",
    "Браузер которым пользуетесь",
    "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft",
    "Скорость интернета",
    "Провайдер",
    "Аттестованный компьютер",
    "Работа с текстом",
    "Работа с картинками, фотографиями",
    "Создание презентаций",
    "Работа с аудио",
    "Работа с видео",
    "Фамилия, инициалы сотрудника",
    "Должность",
]

NUMBERING_ROW = [str(i) for i in range(1, len(COLUMNS) + 1)]

SAMPLE_ROWS: list[list[str]] = [
    [
        "1",
        "МКУ ГИМК",
        "г. Пример, ул. Центральная, 1",
        "Windows 10 Pro",
        "INV-2026-0001",
        "Intel Core i5-12400",
        "2.50",
        "16",
        "SSD",
        "512",
        "Яндекс Браузер",
        "Аккаунт Google, Аккаунт Microsoft",
        "Свыше 100 Мб/с",
        "ПАО Ростелеком",
        "Да",
        "Да",
        "Да",
        "Да",
        "Нет",
        "Нет",
        "Иванов И.И.",
        "Специалист",
    ]
]

_COL_WIDTHS: list[int] = [8, 38, 32, 24, 18, 32, 18, 18, 12, 14, 28, 48, 24, 28, 20, 16, 28, 24, 18, 18, 26, 24]


def build_import_template_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Импорт"

    ws.append(COLUMNS)
    ws.append(NUMBERING_ROW)
    for row in SAMPLE_ROWS:
        ws.append(row)

    for col_idx, width in enumerate(_COL_WIDTHS, start=1):
        col_letter = ws.cell(row=1, column=col_idx).column_letter
        ws.column_dimensions[col_letter].width = width

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
