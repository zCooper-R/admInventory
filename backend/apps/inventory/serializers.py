from rest_framework import serializers

from apps.users.serializers import UserShortSerializer
from apps.locations.serializers import LocationShortSerializer
from .models import Device


class DeviceListSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.__str__", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.__str__", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    device_type_display = serializers.CharField(source="get_device_type_display", read_only=True)

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

    class Meta:
        model = Device
        fields = (
            "id",
            "name",
            "inventory_number",
            "device_type",
            "device_type_display",
            "cpu",
            "ram",
            "storage_type",
            "storage_type_display",
            "storage_size",
            "os",
            "status",
            "status_display",
            "location",
            "location_info",
            "assigned_to",
            "assigned_to_info",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
