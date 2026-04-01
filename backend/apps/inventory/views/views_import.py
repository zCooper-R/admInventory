"""
Excel import / export / template-download views.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from __future__ import annotations

import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.import_export.models import ImportLog
from apps.import_export.services import process_excel_import
from apps.inventory.forms import PCImportForm
from apps.inventory.services.export import export_pcs_to_excel
from apps.inventory.services.template_excel import build_import_template_bytes

logger = logging.getLogger(__name__)


@login_required
def pc_import_template(request):
    """
    Generate and stream the blank Excel import template.

    Delegates to :func:`~apps.inventory.services.template_excel.build_import_template_bytes`,
    the single source of truth shared with the ``create_sample_excel`` management command.
    """
    response = HttpResponse(
        build_import_template_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="import_template.xlsx"'
    return response


@login_required
def pc_import(request):
    """
    Excel import page.

    GET  → show the upload form and the 8 most-recent import logs.
    POST → validate the uploaded file, create an :class:`~apps.import_export.models.ImportLog`
           record, and delegate processing to :func:`~apps.import_export.services.process_excel_import`.
    """
    if request.method == "POST":
        form = PCImportForm(request.POST, request.FILES)
        if form.is_valid():
            log = ImportLog.objects.create(
                file=request.FILES["file"],
                uploaded_by=request.user,
            )
            try:
                process_excel_import(log)
                log.refresh_from_db()
                if log.status in ("success", "partial"):
                    messages.success(
                        request,
                        f"Импорт завершён: создано {log.created_count}, "
                        f"обновлено {log.updated_count}, ошибок {log.error_count}.",
                    )
                else:
                    messages.error(
                        request,
                        "Импорт завершился с ошибкой. Проверьте формат файла.",
                    )
            except Exception as exc:
                logger.exception("Excel import failed")
                messages.error(request, f"Ошибка при обработке файла: {exc}")
            return redirect("pc-import")
    else:
        form = PCImportForm()

    return render(
        request,
        "inventory/pc_import.html",
        {
            "nav_active": "import",
            "form": form,
            "recent_logs": ImportLog.objects.select_related("uploaded_by").order_by(
                "-created_at"
            )[:8],
        },
    )


@login_required
def pc_export(request):
    """
    Generate and stream an Excel workbook containing all PC devices.

    The filename is ``computers_YYYYMMDD_HHMMSS.xlsx`` and is served
    as a browser download attachment.
    """
    try:
        excel_bytes = export_pcs_to_excel()
        filename = f"computers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response = HttpResponse(
            excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as exc:
        logger.exception("Excel export failed")
        messages.error(request, f"Ошибка экспорта: {exc}")
        return redirect("pc-list")
