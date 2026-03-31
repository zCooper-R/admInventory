"""
Django Admin configuration for the Inventory app.

Registered models:
* DeviceAdmin     — full CRUD for all device types with filters and fieldsets.
* SystemSettingsAdmin — singleton editor for operational parameters.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from django.contrib import admin
from .models import Browser, Device, Position, SystemSettings


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number",
        "name",
        "organization",
        "position",
        "browser",
        "device_type",
        "status",
        "location",
        "cpu",
        "ram",
        "os",
        "updated_at",
    )
    list_filter = (
        "status",
        "device_type",
        "storage_type",
        "organization",
        "position",
        "browser",
        "internet_speed",
        "location__organization",
        "location",
    )
    search_fields = (
        "name",
        "inventory_number",
        "cpu",
        "os",
        "employee_name",
        "provider",
        "organization__name",
        "position__name",
        "browser__name",
    )
    list_select_related = ("organization", "position", "browser", "location__organization", "assigned_to")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("inventory_number",)
    autocomplete_fields = ("organization", "position", "browser", "location", "assigned_to")

    fieldsets = (
        (
            "Идентификация",
            {
                "fields": ("name", "inventory_number", "device_type", "status", "organization"),
            },
        ),
        (
            "Характеристики",
            {
                "fields": (
                    "cpu",
                    "cpu_frequency_ghz",
                    "ram",
                    "storage_type",
                    "storage_size",
                    "os",
                    "browser",
                    "internet_speed",
                    "provider",
                ),
            },
        ),
        (
            "Назначение",
            {
                "fields": ("employee_name", "position", "location", "assigned_to"),
            },
        ),
        (
            "Признаки использования",
            {
                "fields": (
                    "has_google_account",
                    "has_apple_account",
                    "has_microsoft_account",
                    "is_attested",
                    "uses_text",
                    "uses_images",
                    "uses_presentations",
                    "uses_audio",
                    "uses_video",
                ),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "organization",
            "position",
            "browser",
            "location__organization",
            "assigned_to",
        )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "created_at")


@admin.register(Browser)
class BrowserAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "created_at")


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Admin panel for the singleton SystemSettings model.

    Prevents creation of additional rows (only pk=1 is meaningful).
    """

    fieldsets = (
        ("Оформление", {"fields": ("system_title", "system_subtitle")}),
        ("Критерии замены", {"fields": ("pc_min_ram_gb", "pc_max_age_years")}),
        ("Бюджет", {"fields": ("pc_price_default",)}),
    )

    def has_add_permission(self, request):
        """Disallow creating additional settings rows from the admin."""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Disallow deleting the singleton settings row."""
        return False
