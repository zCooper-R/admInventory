from django.contrib import admin
from django.db.models import QuerySet
from django.utils.html import format_html

from .models import Browser, Device, Position, ReplacementStatus, SystemSettings


@admin.register(Browser)
class BrowserAdmin(admin.ModelAdmin):
    search_fields = ("name", "normalized_name")
    list_display = ("name", "normalized_name", "created_at")
    ordering = ("name",)
    list_per_page = 30


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    search_fields = ("name", "normalized_name")
    list_display = ("name", "normalized_name", "created_at")
    ordering = ("name",)
    list_per_page = 30


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number_link",
        "organization",
        "employee_name",
        "position",
        "os",
        "hardware_badge",
        "replacement_badge",
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
        "is_certified",
    )
    search_fields = (
        "inventory_number",
        "employee_name",
        "organization__name",
        "position__name",
        "cpu_model",
        "os",
    )
    list_select_related = ("organization", "position", "browser")
    readonly_fields = (
        "replacement_status",
        "replacement_score",
        "replacement_reason",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("organization", "position", "browser")
    ordering = ("inventory_number", "id")
    list_per_page = 50
    save_on_top = True
    date_hierarchy = "updated_at"
    actions = ("recalculate_replacement_for_selected",)
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    ("inventory_number", "device_type"),
                    ("organization", "employee_name"),
                    ("position", "browser"),
                    "os",
                )
            },
        ),
        (
            "Железо",
            {
                "fields": (
                    ("cpu_model", "cpu_frequency"),
                    ("ram", "storage_type", "storage_size"),
                )
            },
        ),
        (
            "Сеть и аккаунты",
            {
                "fields": (
                    ("internet_speed", "provider"),
                    (
                        "has_google_account",
                        "has_apple_account",
                        "has_microsoft_account",
                    ),
                )
            },
        ),
        (
            "Использование",
            {
                "fields": (
                    ("is_certified", "use_for_text", "use_for_images"),
                    ("use_for_presentations", "use_for_audio", "use_for_video"),
                )
            },
        ),
        (
            "Оценка замены",
            {
                "fields": (
                    ("replacement_status", "replacement_score"),
                    "replacement_reason",
                )
            },
        ),
        (
            "Сервисные поля",
            {
                "classes": ("collapse",),
                "fields": (
                    ("serial_number", "purchase_date"),
                    ("agent_hostname", "last_sync"),
                    ("created_at", "updated_at"),
                ),
            },
        ),
    )

    @admin.display(description="Инв. №")
    def inventory_number_link(self, obj: Device) -> str:
        if not obj.inventory_number:
            return "—"
        return format_html(
            '<strong style="color:#1d4ed8;">{}</strong>',
            obj.inventory_number,
        )

    @admin.display(description="Характеристики")
    def hardware_badge(self, obj: Device) -> str:
        ram = f"{obj.ram} ГБ" if obj.ram is not None else "—"
        disk_size = f"{obj.storage_size} ГБ" if obj.storage_size else "—"
        return f"{ram} / {obj.storage_type or '—'} {disk_size}"

    @admin.display(description="Статус замены")
    def replacement_badge(self, obj: Device) -> str:
        colors = {
            ReplacementStatus.REPLACE: "#dc2626",
            ReplacementStatus.ATTENTION: "#d97706",
            ReplacementStatus.OK: "#16a34a",
        }
        color = colors.get(obj.replacement_status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:999px;'
            'font-weight:600;">{} ({})</span>',
            color,
            obj.get_replacement_status_display(),
            obj.replacement_score,
        )

    @admin.action(description="Пересчитать статус замены для выбранных устройств")
    def recalculate_replacement_for_selected(
        self, request, queryset: QuerySet[Device]
    ) -> None:
        updated = 0
        for device in queryset:
            device.save()
            updated += 1
        self.message_user(request, f"Пересчитано устройств: {updated}")


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Оформление", {"fields": ("system_title", "system_subtitle")}),
        ("Бюджет", {"fields": ("pc_price_default",)}),
        (
            "Пороговые параметры",
            {"fields": ("pc_min_ram_gb", "pc_max_age_years")},
        ),
        (
            "Логика замены: ОЗУ",
            {
                "fields": (
                    ("replacement_ram_low_threshold_gb", "replacement_ram_low_score"),
                    ("replacement_ram_mid_threshold_gb", "replacement_ram_mid_score"),
                    ("replacement_ram_high_threshold_gb", "replacement_ram_high_score"),
                    ("replacement_ram_top_score",),
                )
            },
        ),
        (
            "Логика замены: Накопитель",
            {
                "fields": (
                    ("replacement_storage_hdd_score", "replacement_storage_ssd_score"),
                )
            },
        ),
        (
            "Логика замены: Процессор",
            {
                "fields": (
                    ("replacement_cpu_weak_score", "replacement_cpu_medium_score"),
                    ("replacement_cpu_good_score", "replacement_cpu_excellent_score"),
                    ("replacement_cpu_unknown_score",),
                )
            },
        ),
        (
            "Логика замены: Пороги статусов",
            {
                "fields": (
                    ("replacement_attention_threshold", "replacement_ok_threshold"),
                )
            },
        ),
    )
    save_on_top = True

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
