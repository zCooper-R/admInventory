from django.contrib import admin

from .models import Browser, Device, Position, SystemSettings


@admin.register(Browser)
class BrowserAdmin(admin.ModelAdmin):
    search_fields = ("name", "normalized_name")
    list_display = ("name", "normalized_name", "created_at")
    ordering = ("name",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    search_fields = ("name", "normalized_name")
    list_display = ("name", "normalized_name", "created_at")
    ordering = ("name",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number",
        "organization",
        "name",
        "status",
        "storage_type",
        "ram",
        "os",
        "browser",
        "position",
        "updated_at",
    )
    list_filter = (
        "status",
        "device_type",
        "storage_type",
        "organization",
        "browser",
        "position",
        "internet_speed",
    )
    search_fields = (
        "name",
        "inventory_number",
        "employee_name",
        "cpu",
        "os",
        "internet_provider",
    )
    list_select_related = ("organization", "location__organization", "assigned_to", "browser", "position")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("inventory_number", "id")
    autocomplete_fields = ("organization", "location", "assigned_to", "browser", "position")


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Оформление", {"fields": ("system_title", "system_subtitle")}),
        ("Критерии замены", {"fields": ("pc_min_ram_gb", "pc_max_age_years")}),
        ("Бюджет", {"fields": ("pc_price_default",)}),
    )

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
