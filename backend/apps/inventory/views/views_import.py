"""
Excel import / template-download views.
"""

from __future__ import annotations

import logging

from apps.import_export.models import ImportLog
from apps.import_export.services import process_excel_import
from apps.inventory.forms import PCImportForm
from apps.inventory.services.template_excel import build_import_template_bytes
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)


@login_required
def pc_import_template(request):
    response = HttpResponse(
        build_import_template_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="import_template.xlsx"'
    return response


@login_required
def pc_import(request):
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
