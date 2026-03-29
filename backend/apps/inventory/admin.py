"""
Django Admin configuration for the Inventory app.

Registered models:
* DeviceAdmin     — full CRUD for all device types with filters and fieldsets.
* SystemSettingsAdmin — singleton editor for operational parameters.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from django.contrib import admin
from .models import Device, SystemSettings


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number",
        "name",
        "device_type",
        "status",
        "location",
        "assigned_to",
        "cpu",
        "ram",
        "os",
        "updated_at",
    )
    list_filter = ("status", "device_type", "storage_type", "location__organization", "location")
    search_fields = ("name", "inventory_number", "cpu", "os", "assigned_to__full_name", "assigned_to__username")
    list_select_related = ("location__organization", "assigned_to")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("inventory_number",)

    fieldsets = (
        (
            "Идентификация",
            {
                "fields": ("name", "inventory_number", "device_type", "status"),
            },
        ),
        (
            "Характеристики",
            {
                "fields": ("cpu", "ram", "storage_type", "storage_size", "os"),
            },
        ),
        (
            "Назначение",
            {
                "fields": ("location", "assigned_to"),
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
        return super().get_queryset(request).select_related("location__organization", "assigned_to")


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
