from rest_framework import serializers

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "normalized_name", "address", "created_at")
        read_only_fields = ("normalized_name", "created_at")
