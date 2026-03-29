"""
Excel export service for PC devices.

Public API
----------
``export_pcs_to_excel() -> bytes``
    Fetch all ``DeviceType.PC`` records from the database and serialize
    them into an in-memory ``.xlsx`` file using pandas + openpyxl.
    Returns the raw bytes suitable for streaming in an ``HttpResponse``.

Usage::

    excel_bytes = export_pcs_to_excel()
    response = HttpResponse(excel_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="computers.xlsx"'

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
import io
import logging
from datetime import datetime

import pandas as pd

from apps.inventory.models import Device, DeviceType

logger = logging.getLogger(__name__)


def export_pcs_to_excel() -> bytes:
    """
    Export all PC-type devices to an Excel file.
    Returns bytes ready for an HttpResponse.
    """
    pcs = (
        Device.objects.filter(device_type=DeviceType.PC)
        .select_related("location__organization", "assigned_to")
        .order_by("inventory_number")
    )

    logger.info("Exporting %d PC records to Excel", pcs.count())

    rows = []
    for pc in pcs:
        storage = ""
        if pc.storage_type and pc.storage_type != "None":
            storage = pc.storage_type
            if pc.storage_size:
                storage += f" {pc.storage_size} ГБ"

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
                "organization": pc.location.organization.name if pc.location else "",
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
        "Тип накопителя",
        "Объём накопителя (ГБ)",
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
