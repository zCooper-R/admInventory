"""Single-row import processing."""
from __future__ import annotations

from typing import Any

from apps.inventory.models import Device, DeviceStatus, DeviceType, InternetSpeed, StorageType

from .constants import (
    ALLOWED_INTERNET_SPEEDS,
    ALLOWED_STORAGE_TYPES,
    COL_ACCOUNTS,
    COL_ATTESTED,
    COL_BROWSER,
    COL_CPU,
    COL_CPU_FREQ,
    COL_EMPLOYEE,
    COL_INTERNET_SPEED,
    COL_INVENTORY,
    COL_ORGANIZATION,
    COL_OS,
    COL_POSITION,
    COL_PROVIDER,
    COL_RAM,
    COL_STORAGE_SIZE,
    COL_STORAGE_TYPE,
    COL_USES_AUDIO,
    COL_USES_IMAGES,
    COL_USES_PRESENTATIONS,
    COL_USES_TEXT,
    COL_USES_VIDEO,
)
from .normalizers import clean_text, is_blank, parse_accounts, parse_bool, parse_decimal, parse_int
from .resolvers import resolve_browser, resolve_organization, resolve_position


class RowValidationError(Exception):
    pass


def _require_text(row: dict[str, Any], column: str) -> str:
    value = clean_text(row.get(column))
    if not value:
        raise RowValidationError(f"Пустое обязательное поле: {column}")
    return value


def _require_int(row: dict[str, Any], column: str) -> int:
    value = parse_int(row.get(column))
    if value is None:
        raise RowValidationError(f"Некорректное обязательное поле: {column}")
    return value


def _storage_type(row: dict[str, Any]) -> str:
    value = _require_text(row, COL_STORAGE_TYPE).upper()
    if value not in ALLOWED_STORAGE_TYPES:
        raise RowValidationError(f"Недопустимый тип диска: '{value}'. Ожидается SSD или HDD")
    return StorageType.SSD if value == "SSD" else StorageType.HDD


def _internet_speed(row: dict[str, Any]) -> str:
    value = clean_text(row.get(COL_INTERNET_SPEED))
    if not value:
        return ""
    if value not in ALLOWED_INTERNET_SPEEDS:
        raise RowValidationError(f"Недопустимая скорость интернета: '{value}'")
    return value


def process_row(row_num: int, row: dict[str, Any]) -> tuple[bool, str | None]:
    inventory_number = _require_text(row, COL_INVENTORY)
    organization_name = _require_text(row, COL_ORGANIZATION)
    os_name = _require_text(row, COL_OS)
    ram = _require_int(row, COL_RAM)
    storage_type = _storage_type(row)

    organization = resolve_organization(organization_name)
    position = resolve_position(clean_text(row.get(COL_POSITION)))
    browser = resolve_browser(clean_text(row.get(COL_BROWSER)))

    has_google, has_apple, has_microsoft = parse_accounts(row.get(COL_ACCOUNTS))

    defaults = {
        "name": f"Устройство {inventory_number}",
        "device_type": DeviceType.PC,
        "status": DeviceStatus.ACTIVE,
        "organization": organization,
        "assigned_to": None,
        "location": None,
        "os": os_name,
        "cpu": clean_text(row.get(COL_CPU)),
        "cpu_frequency_ghz": parse_decimal(row.get(COL_CPU_FREQ)),
        "ram": ram,
        "storage_type": storage_type,
        "storage_size": parse_int(row.get(COL_STORAGE_SIZE)),
        "browser": browser,
        "has_google_account": has_google,
        "has_apple_account": has_apple,
        "has_microsoft_account": has_microsoft,
        "internet_speed": _internet_speed(row),
        "provider": clean_text(row.get(COL_PROVIDER)),
        "is_attested": parse_bool(row.get(COL_ATTESTED)),
        "uses_text": parse_bool(row.get(COL_USES_TEXT)),
        "uses_images": parse_bool(row.get(COL_USES_IMAGES)),
        "uses_presentations": parse_bool(row.get(COL_USES_PRESENTATIONS)),
        "uses_audio": parse_bool(row.get(COL_USES_AUDIO)),
        "uses_video": parse_bool(row.get(COL_USES_VIDEO)),
        "employee_name": clean_text(row.get(COL_EMPLOYEE)),
        "position": position,
    }

    device = Device.objects.filter(inventory_number=inventory_number).first()
    if device is None:
        Device.objects.create(inventory_number=inventory_number, **defaults)
        return True, None

    for field, value in defaults.items():
        setattr(device, field, value)
    device.save()
    return False, None
