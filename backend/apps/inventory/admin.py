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
        "employee_name",
        "position",
        "browser",
        "ram",
        "storage_type",
        "replacement_status",
        "replacement_score",
        "updated_at",
    )
    list_filter = (
        "organization",
        "position",
        "browser",
        "replacement_status",
        "storage_type",
        "internet_speed",
        "has_google_account",
        "has_apple_account",
        "has_microsoft_account",
    )
    search_fields = ("inventory_number", "employee_name", "organization__name", "position__name", "cpu_model", "os")
    list_select_related = ("organization", "position", "browser")
    readonly_fields = ("replacement_status", "replacement_score", "replacement_reason", "created_at", "updated_at")
    ordering = ("inventory_number", "id")
    autocomplete_fields = ("organization", "position", "browser")


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Оформление", {"fields": ("system_title", "system_subtitle")}),
        ("Пороговые параметры", {"fields": ("pc_min_ram_gb", "pc_max_age_years")}),
        ("Бюджет", {"fields": ("pc_price_default",)}),
    )

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
