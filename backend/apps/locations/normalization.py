import re
from typing import Iterable

SPACES_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^0-9a-zа-я]+", flags=re.IGNORECASE)

# Common legal-form phrase mappings.
PHRASE_ALIASES: tuple[tuple[str, str], ...] = (
    ("муниципальное бюджетное общеобразовательное учреждение", "мбоу"),
    ("муниципальное бюджетное учреждение", "мбу"),
    ("муниципальное казенное учреждение", "мку"),
    ("муниципальное казённое учреждение", "мку"),
    ("муниципальное автономное учреждение", "мау"),
    ("государственное бюджетное учреждение", "гбу"),
)


def _cleanup(value: str) -> str:
    text = (value or "").strip().lower().replace("ё", "е")
    text = NON_ALNUM_RE.sub(" ", text)
    text = SPACES_RE.sub(" ", text).strip()
    return text


def _extract_acronym(words: Iterable[str]) -> str:
    parts = [w for w in words if w and w not in {"имени", "им", "г", "города"}]
    if len(parts) < 2:
        return ""
    return "".join(word[0] for word in parts if word)


def normalize_organization_name(value: str) -> str:
    """Normalize organization names so abbreviations and full forms deduplicate."""
    text = _cleanup(value)
    if not text:
        return ""

    for src, dst in PHRASE_ALIASES:
        if src in text:
            text = text.replace(src, dst)

    parts = text.split()
    if not parts:
        return ""

    legal_forms = {"мку", "мбу", "мбоу", "мау", "гбу"}
    if parts[0] in legal_forms:
        legal_form = parts[0]
        rest = parts[1:]
        if not rest:
            return legal_form
        if len(rest) == 1:
            return f"{legal_form} {rest[0]}".strip()
        acronym = _extract_acronym(rest)
        if acronym:
            return f"{legal_form} {acronym}".strip()

    return " ".join(parts)
