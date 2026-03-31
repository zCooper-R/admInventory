from django.contrib import admin
from .models import Organization, Location


class LocationInline(admin.TabularInline):
    model = Location
    extra = 1
    fields = ("name", "address")
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "normalized_name", "address", "location_count", "created_at")
    search_fields = ("name", "normalized_name")
    inlines = [LocationInline]

    @admin.display(description="Площадок")
    def location_count(self, obj):
        return obj.locations.count()


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "address", "created_at")
    list_filter = ("organization",)
    search_fields = ("name", "address", "organization__name")
    list_select_related = ("organization",)
    autocomplete_fields = ("organization",)
