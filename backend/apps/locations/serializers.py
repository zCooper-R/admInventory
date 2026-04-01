from rest_framework import serializers
from .models import Organization, Location


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "normalized_name", "address", "created_at")
        read_only_fields = ("created_at",)


class LocationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = Location
        fields = (
            "id",
            "name",
            "address",
            "organization",
            "organization_name",
            "created_at",
        )
        read_only_fields = ("created_at",)


class LocationShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name", "organization")
