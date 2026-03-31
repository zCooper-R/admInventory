"""Excel export service for PC devices."""

import io
import logging

import pandas as pd

from apps.inventory.models import Device, DeviceType

logger = logging.getLogger(__name__)


def export_pcs_to_excel() -> bytes:
    pcs = (
        Device.objects.filter(device_type=DeviceType.PC)
        .select_related("organization", "location__organization", "assigned_to")
        .order_by("inventory_number")
    )

    logger.info("Exporting %d PC records to Excel", pcs.count())

    rows = []
    for pc in pcs:
        rows.append(
            {
                "inventory_number": pc.inventory_number,
                "name": pc.name,
                "cpu": pc.cpu or "",
                "ram": pc.ram if pc.ram is not None else "",
                "storage_type": pc.storage_type or "",
                "storage_size": pc.storage_size if pc.storage_size is not None else "",
                "os": pc.os or "",
                "status": pc.get_status_display(),
                "location": pc.location.name if pc.location else "",
                "organization": pc.organization.name if pc.organization_id else "",
                "assigned_to": str(pc.assigned_to) if pc.assigned_to else "",
            }
        )

    df = pd.DataFrame(
        rows,
        columns=[
            "inventory_number",
            "name",
            "cpu",
            "ram",
            "storage_type",
            "storage_size",
            "os",
            "status",
            "location",
            "organization",
            "assigned_to",
        ],
    )

    df.columns = [
        "Инвентарный номер",
        "Наименование",
        "Процессор",
        "ОЗУ (ГБ)",
        "Тип диска",
        "Емкость диска (ГБ)",
        "Операционная система",
        "Статус",
        "Площадка",
        "Организация",
        "Назначен",
    ]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Компьютеры")

        ws = writer.sheets["Компьютеры"]
        col_widths = [20, 20, 25, 10, 15, 22, 25, 12, 20, 25, 25]
        for i, width in enumerate(col_widths, start=1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    buffer.seek(0)
    return buffer.read()
