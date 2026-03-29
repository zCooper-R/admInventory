import django_filters
from .models import Device


class DeviceFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Device.status.field.choices)
    device_type = django_filters.ChoiceFilter(choices=Device.device_type.field.choices)
    location = django_filters.NumberFilter(field_name="location__id")
    organization = django_filters.NumberFilter(field_name="location__organization__id")
    ram_min = django_filters.NumberFilter(field_name="ram", lookup_expr="gte")
    ram_max = django_filters.NumberFilter(field_name="ram", lookup_expr="lte")

    class Meta:
        model = Device
        fields = ["status", "device_type", "location", "organization", "storage_type"]
