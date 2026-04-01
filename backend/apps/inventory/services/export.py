from __future__ import annotations

import io
from decimal import Decimal

from apps.inventory.models import Device, DeviceType
from apps.inventory.services.template_excel import COLUMNS, NUMBERING_ROW
from openpyxl import Workbook


def _bool_to_yes_no(value: bool | None) -> str:
    if value is True:
        return "Да"
    if value is False:
        return "Нет"
    return ""


def _accounts_to_text(device: Device) -> str:
    parts: list[str] = []
    if device.has_google_account:
        parts.append("Аккаунт Google")
    if device.has_apple_account:
        parts.append("Аккаунт Apple")
    if device.has_microsoft_account:
        parts.append("Аккаунт Microsoft")

    if parts:
        return ", ".join(parts)

    # Explicitly write "Нет" only when all flags are explicitly False.
    flags = (
        device.has_google_account,
        device.has_apple_account,
        device.has_microsoft_account,
    )
    if all(flag is False for flag in flags):
        return "Нет"
    return ""


def _frequency_to_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def export_pcs_to_excel() -> bytes:
    devices = (
        Device.objects.filter(device_type=DeviceType.PC)
        .select_related("organization", "browser", "position")
        .order_by("organization__name", "inventory_number")
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Импорт"

    ws.append(COLUMNS)
    ws.append(NUMBERING_ROW)

    for idx, d in enumerate(devices, start=1):
        ws.append(
            [
                str(idx),
                d.organization.name,
                d.organization.address or "",
                d.os or "",
                d.inventory_number or "",
                d.cpu_model or "",
                _frequency_to_text(d.cpu_frequency),
                d.ram if d.ram is not None else "",
                d.storage_type or "",
                d.storage_size if d.storage_size is not None else "",
                d.browser.name if d.browser else "",
                _accounts_to_text(d),
                d.get_internet_speed_display() if d.internet_speed else "",
                d.provider or "",
                _bool_to_yes_no(d.is_certified),
                _bool_to_yes_no(d.use_for_text),
                _bool_to_yes_no(d.use_for_images),
                _bool_to_yes_no(d.use_for_presentations),
                _bool_to_yes_no(d.use_for_audio),
                _bool_to_yes_no(d.use_for_video),
                d.employee_name or "",
                d.position.name if d.position else "",
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
