from __future__ import annotations

import logging
from dataclasses import dataclass

from apps.inventory.models import Device, DeviceType
from django.db import transaction

from .normalizers import (
    normalize_text,
    parse_accounts,
    parse_bool,
    parse_frequency,
    parse_internet_speed,
    parse_positive_int,
    parse_storage_type,
)
from .resolvers import BrowserResolver, OrganizationResolver, PositionResolver
from .types import ParsedRow

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RowApplyResult:
    created: bool


MANDATORY_FIELDS = {
    "organization_name": "организация",
    "inventory_number": "инвентарный номер",
    "os": "наименование ОС",
    "ram": "оперативная память",
    "storage_type": "тип диска",
}


def _require_non_empty(values: dict[str, str], key: str) -> str:
    val = normalize_text(values.get(key, ""))
    if not val:
        raise ValueError(f"Не заполнено обязательное поле: {MANDATORY_FIELDS[key]}")
    return val


@transaction.atomic
def process_row(parsed_row: ParsedRow) -> RowApplyResult:
    values = parsed_row.values

    organization_name = _require_non_empty(values, "organization_name")
    inventory_number = _require_non_empty(values, "inventory_number")
    os_name = _require_non_empty(values, "os")

    ram = parse_positive_int(values.get("ram", ""))
    if ram is None:
        raise ValueError("Оперативная память должна быть числом")

    storage_type = parse_storage_type(values.get("storage_type", ""))
    if not storage_type:
        raise ValueError("Тип диска должен быть SSD или HDD")

    organization = OrganizationResolver.resolve_or_create(
        organization_name, values.get("organization_address", "")
    )
    position = PositionResolver.resolve_or_create(values.get("position", ""))
    browser = BrowserResolver.resolve_or_create(values.get("browser", ""))

    has_google, has_apple, has_microsoft = parse_accounts(values.get("accounts", ""))

    values_to_apply = {
        "organization": organization,
        "device_type": DeviceType.PC,
        "os": os_name,
        "cpu_model": normalize_text(values.get("cpu_model", "")),
        "cpu_frequency": parse_frequency(values.get("cpu_frequency", "")),
        "ram": ram,
        "storage_type": storage_type,
        "storage_size": parse_positive_int(values.get("storage_size", "")),
        "browser": browser,
        "has_google_account": has_google,
        "has_apple_account": has_apple,
        "has_microsoft_account": has_microsoft,
        "internet_speed": parse_internet_speed(values.get("internet_speed", "")),
        "provider": normalize_text(values.get("provider", "")),
        "is_certified": parse_bool(values.get("is_certified", "")),
        "use_for_text": parse_bool(values.get("use_for_text", "")),
        "use_for_images": parse_bool(values.get("use_for_images", "")),
        "use_for_presentations": parse_bool(values.get("use_for_presentations", "")),
        "use_for_audio": parse_bool(values.get("use_for_audio", "")),
        "use_for_video": parse_bool(values.get("use_for_video", "")),
        "employee_name": normalize_text(values.get("employee_name", "")),
        "position": position,
    }

    device = Device.objects.filter(inventory_number=inventory_number).first()
    created = device is None
    if created:
        device = Device(inventory_number=inventory_number, organization=organization)
        logger.debug(
            "Создаётся новое устройство: row=%s inventory=%s",
            parsed_row.row_number,
            inventory_number,
        )
    else:
        logger.debug(
            "Обновляется устройство: row=%s inventory=%s",
            parsed_row.row_number,
            inventory_number,
        )

    for field_name, field_value in values_to_apply.items():
        setattr(device, field_name, field_value)
    device.save()

    logger.info(
        "Строка обработана: row=%s inventory=%s action=%s organization=%s",
        parsed_row.row_number,
        inventory_number,
        "create" if created else "update",
        organization.name,
    )

    return RowApplyResult(created=created)
