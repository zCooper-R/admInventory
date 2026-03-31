from rest_framework import serializers

from apps.users.serializers import UserShortSerializer
from apps.locations.serializers import LocationShortSerializer
from .models import Device


class DeviceListSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.__str__", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.__str__", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    device_type_display = serializers.CharField(source="get_device_type_display", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "name",
            "inventory_number",
            "device_type",
            "device_type_display",
            "status",
            "status_display",
            "organization",
            "organization_name",
            "location",
            "location_name",
            "assigned_to",
            "assigned_to_name",
            "updated_at",
        )


class DeviceDetailSerializer(serializers.ModelSerializer):
    location_info = LocationShortSerializer(source="location", read_only=True)
    assigned_to_info = UserShortSerializer(source="assigned_to", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    device_type_display = serializers.CharField(source="get_device_type_display", read_only=True)
    storage_type_display = serializers.CharField(source="get_storage_type_display", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    browser_name = serializers.CharField(source="browser.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "name",
            "inventory_number",
            "device_type",
            "device_type_display",
            "organization",
            "organization_name",
            "location",
            "location_info",
            "cpu",
            "cpu_frequency",
            "ram",
            "storage_type",
            "storage_type_display",
            "storage_size",
            "os",
            "browser",
            "browser_name",
            "employee_name",
            "position",
            "position_name",
            "has_google_account",
            "has_apple_account",
            "has_microsoft_account",
            "internet_speed",
            "internet_provider",
            "is_attested",
            "work_with_text",
            "work_with_images",
            "create_presentations",
            "work_with_audio",
            "work_with_video",
            "status",
            "status_display",
            "assigned_to",
            "assigned_to_info",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_inventory_number(self, value):
        inventory_number = (value or "").strip()
        if not inventory_number:
            return inventory_number

        qs = Device.objects.filter(inventory_number=inventory_number)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Устройство с таким инвентарным номером уже существует.")
        return inventory_number
