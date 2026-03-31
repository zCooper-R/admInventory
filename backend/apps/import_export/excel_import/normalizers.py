from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Iterable

from apps.inventory.models import InternetSpeed, StorageType
from apps.locations.normalization import normalize_organization_name

BOOL_TRUE = {
    "да",
    "есть",
    "true",
    "1",
    "+",
    "y",
    "yes",
}
BOOL_FALSE = {
    "нет",
    "отсутствует",
    "false",
    "0",
    "-",
    "n",
    "no",
}

INTERNET_SPEED_ALIASES: dict[str, str] = {
    "до 5 мб/с": InternetSpeed.UP_TO_5,
    "от 5 до 50 мб/с": InternetSpeed.FROM_5_TO_50,
    "от 50 до 100 мб/с": InternetSpeed.FROM_50_TO_100,
    "свыше 100 мб/с": InternetSpeed.ABOVE_100,
}

STORAGE_ALIASES: dict[str, str] = {
    "ssd": StorageType.SSD,
    "hdd": StorageType.HDD,
}

ACCOUNT_ALIASES: dict[str, str] = {
    "google": "google",
    "аккаунт google": "google",
    "apple": "apple",
    "аккаунт apple": "apple",
    "microsoft": "microsoft",
    "аккаунт microsoft": "microsoft",
}


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def normalize_lookup(value: str) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def normalize_position(value: str) -> str:
    return normalize_lookup(value)


def normalize_browser(value: str) -> str:
    return normalize_lookup(value)


def normalize_org(value: str) -> str:
    return normalize_organization_name(value)


def parse_bool(value: str) -> bool | None:
    normalized = normalize_lookup(value)
    if not normalized:
        return None
    if normalized in BOOL_TRUE:
        return True
    if normalized in BOOL_FALSE:
        return False
    return None


def parse_positive_int(value: str) -> int | None:
    normalized = normalize_text(value).replace(",", ".")
    if not normalized:
        return None
    try:
        number = int(float(normalized))
    except ValueError:
        return None
    return number if number >= 0 else None


def parse_frequency(value: str) -> Decimal | None:
    normalized = normalize_text(value).replace(",", ".")
    if not normalized:
        return None
    try:
        parsed = Decimal(normalized)
    except InvalidOperation:
        return None
    if parsed < 0:
        return None
    return parsed.quantize(Decimal("0.01"))


def parse_storage_type(value: str) -> str | None:
    normalized = normalize_lookup(value)
    return STORAGE_ALIASES.get(normalized)


def parse_internet_speed(value: str) -> str | None:
    normalized = normalize_lookup(value)
    return INTERNET_SPEED_ALIASES.get(normalized)


def _extract_account_tokens(value: str) -> Iterable[str]:
    prepared = normalize_lookup(value)
    if not prepared:
        return []
    chunks = [part.strip() for part in re.split(r"[,;]| и ", prepared) if part.strip()]
    return chunks


def parse_accounts(value: str) -> tuple[bool | None, bool | None, bool | None]:
    normalized = normalize_lookup(value)
    if not normalized:
        return None, None, None
    if normalized in BOOL_FALSE or "отсутствует" in normalized:
        return False, False, False

    google = False
    apple = False
    microsoft = False

    for token in _extract_account_tokens(value):
        mapped = ACCOUNT_ALIASES.get(token)
        if mapped == "google":
            google = True
        elif mapped == "apple":
            apple = True
        elif mapped == "microsoft":
            microsoft = True

    if not any([google, apple, microsoft]):
        bool_val = parse_bool(value)
        if bool_val is None:
            return None, None, None
        return bool_val, bool_val, bool_val

    return google, apple, microsoft
