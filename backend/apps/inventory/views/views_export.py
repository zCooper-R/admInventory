from __future__ import annotations

import logging
from datetime import datetime

from apps.import_export.services import (
    export_organization_budget_to_excel,
    export_pcs_to_excel,
)
from apps.inventory.models import Device, DeviceType, ReplacementStatus
from apps.inventory.services.budget_report import (
    build_organization_budget_report_rows,
    resolve_pc_price,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

logger = logging.getLogger(__name__)


def _xlsx_response(payload: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(payload, content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def pc_export(request):
    """
    Generate and stream an Excel workbook containing PC devices.

    This endpoint keeps the original import-compatible workbook format.
    """
    try:
        queryset = Device.objects.filter(device_type=DeviceType.PC)
        organization_id = request.GET.get("organization", "").strip()
        replacement_status = request.GET.get("replacement_status", "").strip()
        storage_type = request.GET.get("storage_type", "").strip()

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if replacement_status in {
            ReplacementStatus.OK,
            ReplacementStatus.ATTENTION,
            ReplacementStatus.REPLACE,
        }:
            queryset = queryset.filter(replacement_status=replacement_status)
        if storage_type in {"SSD", "HDD"}:
            queryset = queryset.filter(storage_type=storage_type)

        excel_bytes = export_pcs_to_excel(queryset=queryset)
        filename = f"computers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return _xlsx_response(excel_bytes, filename)
    except Exception as exc:
        logger.exception("Excel export failed")
        messages.error(request, f"Ошибка экспорта: {exc}")
        return redirect("pc-list")


@login_required
def organization_budget_export(request):
    price = resolve_pc_price(request.GET.get("price"))
    rows = build_organization_budget_report_rows(price)
    excel_bytes = export_organization_budget_to_excel(rows, price)
    filename = (
        f"organization_budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    logger.info(
        "Сформирован отчёт по организациям: user=%s price=%s rows=%s",
        request.user.username,
        price,
        len(rows),
    )
    return _xlsx_response(excel_bytes, filename)
