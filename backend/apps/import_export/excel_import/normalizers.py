"""Normalization and parsing helpers for Excel import."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

TRUE_VALUES = {"да", "есть", "+", "true", "1", "y", "yes"}
FALSE_VALUES = {"нет", "-", "false", "0", "n", "no", "отсутствует"}


def is_blank(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def clean_text(value: Any) -> str:
    if is_blank(value):
        return ""
    return str(value).strip()


def parse_int(value: Any) -> int | None:
    if is_blank(value):
        return None
    raw = str(value).strip().replace(",", ".")
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None


def parse_decimal(value: Any) -> Decimal | None:
    if is_blank(value):
        return None
    raw = str(value).strip().replace(",", ".")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def parse_bool(value: Any) -> bool | None:
    if is_blank(value):
        return None

    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def parse_accounts(value: Any) -> tuple[bool | None, bool | None, bool | None]:
    if is_blank(value):
        return (None, None, None)

    normalized = str(value).strip().lower()
    if normalized in {"отсутствует", "нет", "none"}:
        return (False, False, False)

    has_google = "google" in normalized
    has_apple = "apple" in normalized
    has_microsoft = "microsoft" in normalized

    if not any((has_google, has_apple, has_microsoft)):
        return (None, None, None)

    return (has_google, has_apple, has_microsoft)


def normalize_header(value: Any) -> str:
    return clean_text(value)
