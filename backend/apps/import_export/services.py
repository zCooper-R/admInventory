import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from django.db import transaction

from apps.inventory.models import Device, DeviceType, DeviceStatus, StorageType
from apps.locations.models import Location
from apps.users.models import User
from .models import ImportLog, ImportStatus

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "name",
    "inventory_number",
}

COLUMN_MAP = {
    "name": "name",
    "inventory_number": "inventory_number",
    "device_type": "device_type",
    "cpu": "cpu",
    "ram": "ram",
    "storage_type": "storage_type",
    "storage_size": "storage_size",
    "os": "os",
    "status": "status",
    "location": "location",
    "assigned_to": "assigned_to",
}

DEVICE_TYPE_ALIASES: dict[str, str] = {
    "пк": DeviceType.PC,
    "компьютер": DeviceType.PC,
    "pc": DeviceType.PC,
    "ноутбук": DeviceType.LAPTOP,
    "laptop": DeviceType.LAPTOP,
    "принтер": DeviceType.PRINTER,
    "printer": DeviceType.PRINTER,
}

STATUS_ALIASES: dict[str, str] = {
    "активен": DeviceStatus.ACTIVE,
    "active": DeviceStatus.ACTIVE,
    "сломан": DeviceStatus.BROKEN,
    "broken": DeviceStatus.BROKEN,
    "списан": DeviceStatus.WRITE_OFF,
    "write_off": DeviceStatus.WRITE_OFF,
    "write-off": DeviceStatus.WRITE_OFF,
}

STORAGE_TYPE_ALIASES: dict[str, str] = {
    "hdd": StorageType.HDD,
    "ssd": StorageType.SSD,
    "mixed": StorageType.MIXED,
    "hdd+ssd": StorageType.MIXED,
    "hdd + ssd": StorageType.MIXED,
    "none": StorageType.NONE,
    "нет": StorageType.NONE,
}


@dataclass
class RowError:
    row: int
    message: str


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    errors: list[RowError] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.created + self.updated + len(self.errors)


def _normalize(value: Any, aliases: dict[str, str], default: str) -> str:
    if pd.isna(value) or value is None:
        return default
    normalized = str(value).strip().lower()
    return aliases.get(normalized, default)


def _get_location(raw: Any) -> Location | None:
    if pd.isna(raw) or not raw:
        return None
    name = str(raw).strip()
    return Location.objects.filter(name__iexact=name).first()


def _get_user(raw: Any) -> User | None:
    if pd.isna(raw) or not raw:
        return None
    value = str(raw).strip()
    return User.objects.filter(username__iexact=value).first() or \
           User.objects.filter(full_name__iexact=value).first()


def _safe_int(value: Any) -> int | None:
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def process_excel_import(import_log: ImportLog) -> None:
    logger.info("Starting import for ImportLog #%s", import_log.pk)

    import_log.status = ImportStatus.PROCESSING
    import_log.save(update_fields=["status"])

    try:
        df = pd.read_excel(import_log.file.path, dtype=str)
    except Exception as exc:
        logger.error("Failed to read Excel file: %s", exc)
        import_log.status = ImportStatus.FAILED
        import_log.errors = [{"row": 0, "message": f"Не удалось прочитать файл: {exc}"}]
        import_log.save(update_fields=["status", "errors"])
        return

    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        msg = f"Отсутствуют обязательные колонки: {', '.join(missing)}"
        logger.error(msg)
        import_log.status = ImportStatus.FAILED
        import_log.errors = [{"row": 0, "message": msg}]
        import_log.save(update_fields=["status", "errors"])
        return

    import_log.total_rows = len(df)
    result = ImportResult()

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-based + header
        try:
            _process_row(row, result, row_num)
        except Exception as exc:
            logger.exception("Unexpected error on row %s", row_num)
            result.errors.append(RowError(row=row_num, message=str(exc)))

    if result.errors and (result.created > 0 or result.updated > 0):
        import_log.status = ImportStatus.PARTIAL
    elif result.errors:
        import_log.status = ImportStatus.FAILED
    else:
        import_log.status = ImportStatus.SUCCESS

    import_log.created_count = result.created
    import_log.updated_count = result.updated
    import_log.error_count = len(result.errors)
    import_log.errors = [{"row": e.row, "message": e.message} for e in result.errors]
    import_log.save(update_fields=["status", "total_rows", "created_count", "updated_count", "error_count", "errors"])

    logger.info(
        "Import #%s done: created=%s, updated=%s, errors=%s",
        import_log.pk,
        result.created,
        result.updated,
        len(result.errors),
    )


@transaction.atomic
def _process_row(row: pd.Series, result: ImportResult, row_num: int) -> None:
    inventory_number = str(row.get("inventory_number", "")).strip()
    name = str(row.get("name", "")).strip()

    if not inventory_number:
        result.errors.append(RowError(row=row_num, message="Пустой инвентарный номер"))
        return
    if not name:
        result.errors.append(RowError(row=row_num, message="Пустое наименование"))
        return

    location_raw = row.get("location")
    location = _get_location(location_raw)
    if location is None:
        result.errors.append(
            RowError(row=row_num, message=f"Площадка не найдена: '{location_raw}'")
        )
        return

    defaults = {
        "name": name,
        "device_type": _normalize(row.get("device_type"), DEVICE_TYPE_ALIASES, DeviceType.PC),
        "cpu": str(row.get("cpu", "")).strip() if not pd.isna(row.get("cpu", "")) else "",
        "ram": _safe_int(row.get("ram")),
        "storage_type": _normalize(row.get("storage_type"), STORAGE_TYPE_ALIASES, StorageType.HDD),
        "storage_size": _safe_int(row.get("storage_size")),
        "os": str(row.get("os", "")).strip() if not pd.isna(row.get("os", "")) else "",
        "status": _normalize(row.get("status"), STATUS_ALIASES, DeviceStatus.ACTIVE),
        "location": location,
        "assigned_to": _get_user(row.get("assigned_to")),
    }

    device, created = Device.objects.update_or_create(
        inventory_number=inventory_number,
        defaults=defaults,
    )

    if created:
        result.created += 1
        logger.debug("Created device: %s", device)
    else:
        result.updated += 1
        logger.debug("Updated device: %s", device)
