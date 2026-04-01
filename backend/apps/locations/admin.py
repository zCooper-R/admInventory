from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
        "device_count",
        "created_at",
    )
    search_fields = ("name", "normalized_name", "address")
    ordering = ("name",)
    list_per_page = 40

    @admin.display(description="Устройств")
    def device_count(self, obj):
        return obj.devices.count()
