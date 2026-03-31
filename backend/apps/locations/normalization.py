"""Helpers for organization-name normalization used in import deduplication."""
from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^\w\s]", re.UNICODE)

_ABBR_MAP: dict[str, str] = {
    "муниципальное": "м",
    "казенное": "к",
    "казённое": "к",
    "бюджетное": "б",
    "бюджетное": "б",
    "общеобразовательное": "о",
    "учреждение": "у",
}


def normalize_organization_name(value: str) -> str:
    """
    Produce a stable normalized organization key.

    Example:
      - "МКУ ГИМК" -> "мку гимк"
      - "Муниципальное казенное учреждение ГИМК" -> "мку гимк"
    """
    raw = (value or "").strip().lower()
    raw = _NON_WORD_RE.sub(" ", raw)
    raw = _WHITESPACE_RE.sub(" ", raw).strip()

    if not raw:
        return ""

    tokens = raw.split(" ")
    expanded = [_ABBR_MAP.get(token, token) for token in tokens]

    if expanded[:3] == ["м", "к", "у"]:
        expanded = ["мку"] + expanded[3:]
    if expanded[:3] == ["м", "б", "у"]:
        expanded = ["мбу"] + expanded[3:]
    if expanded[:4] == ["м", "б", "о", "у"]:
        expanded = ["мбоу"] + expanded[4:]

    normalized = " ".join(expanded)
    return _WHITESPACE_RE.sub(" ", normalized).strip()
