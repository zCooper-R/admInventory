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
    list_filter = ("status", "created_at")
    search_fields = ("file", "uploaded_by__username", "uploaded_by__email")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 30
    save_on_top = True
    readonly_fields = (
        "uploaded_by",
        "status",
        "total_rows",
        "created_count",
        "updated_count",
        "error_count",
        "errors_preview",
        "errors",
        "created_at",
    )
    fieldsets = (
        ("Файл", {"fields": ("file", "uploaded_by", "created_at")}),
        (
            "Результат",
            {
                "fields": (
                    "status",
                    ("total_rows", "created_count", "updated_count", "error_count"),
                    "errors_preview",
                    "errors",
                )
            },
        ),
    )

    STATUS_COLORS = {
        "pending": "#64748b",
        "processing": "#0284c7",
        "success": "#16a34a",
        "partial": "#d97706",
        "failed": "#dc2626",
    }

    @admin.display(description="Статус")
    def status_badge(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:999px;'
            'font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Ошибки (кратко)")
    def errors_preview(self, obj):
        if not obj.errors:
            return "—"
        first = obj.errors[0]
        text = str(first)
        if len(text) > 180:
            text = f"{text[:180]}..."
        return text

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            try:
                process_excel_import(obj)
            except Exception as exc:
                self.message_user(request, f"Ошибка импорта: {exc}", level="error")
