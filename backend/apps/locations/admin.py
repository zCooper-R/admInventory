from django.contrib import admin

from .models import Location, Organization


class LocationInline(admin.TabularInline):
    model = Location
    extra = 0
    fields = ("name", "address")
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
        "location_count",
        "device_count",
        "created_at",
    )
    search_fields = ("name", "normalized_name", "address")
    ordering = ("name",)
    list_per_page = 40
    inlines = [LocationInline]

    @admin.display(description="Площадок")
    def location_count(self, obj):
        return obj.locations.count()

    @admin.display(description="Устройств")
    def device_count(self, obj):
        return obj.devices.count()


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "address", "created_at")
    list_filter = ("organization",)
    search_fields = ("name", "address", "organization__name")
    list_select_related = ("organization",)
    autocomplete_fields = ("organization",)
    ordering = ("organization__name", "name")
    list_per_page = 40
