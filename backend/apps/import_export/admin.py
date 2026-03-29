from django.contrib import admin
from django.utils.html import format_html

from .models import ImportLog
from .services import process_excel_import


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "file",
        "uploaded_by",
        "status_badge",
        "total_rows",
        "created_count",
        "updated_count",
        "error_count",
        "created_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "uploaded_by",
        "status",
        "total_rows",
        "created_count",
        "updated_count",
        "error_count",
        "errors",
        "created_at",
    )
    ordering = ("-created_at",)

    STATUS_COLORS = {
        "pending": "#6c757d",
        "processing": "#0dcaf0",
        "success": "#198754",
        "partial": "#fd7e14",
        "failed": "#dc3545",
    }

    @admin.display(description="Статус")
    def status_badge(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            try:
                process_excel_import(obj)
            except Exception as exc:
                self.message_user(request, f"Ошибка импорта: {exc}", level="error")
