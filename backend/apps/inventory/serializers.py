from rest_framework import serializers

from .models import Device


class DeviceListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True)
    browser_name = serializers.CharField(source="browser.name", read_only=True)
    replacement_status_display = serializers.CharField(source="get_replacement_status_display", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "inventory_number",
            "organization",
            "organization_name",
            "employee_name",
            "position",
            "position_name",
            "browser",
            "browser_name",
            "replacement_status",
            "replacement_status_display",
            "replacement_score",
            "updated_at",
        )


class DeviceDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True)
    browser_name = serializers.CharField(source="browser.name", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "inventory_number",
            "organization",
            "organization_name",
            "employee_name",
            "position",
            "position_name",
            "browser",
            "browser_name",
            "os",
            "cpu_model",
            "cpu_frequency",
            "ram",
            "storage_type",
            "storage_size",
            "has_google_account",
            "has_apple_account",
            "has_microsoft_account",
            "internet_speed",
            "provider",
            "is_certified",
            "use_for_text",
            "use_for_images",
            "use_for_presentations",
            "use_for_audio",
            "use_for_video",
            "replacement_status",
            "replacement_score",
            "replacement_reason",
            "purchase_date",
            "serial_number",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("replacement_status", "replacement_score", "replacement_reason", "created_at", "updated_at")

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
