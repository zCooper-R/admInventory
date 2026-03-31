import django_filters

from .models import Device


class DeviceFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Device.status.field.choices)
    device_type = django_filters.ChoiceFilter(choices=Device.device_type.field.choices)
    location = django_filters.NumberFilter(field_name="location__id")
    organization = django_filters.NumberFilter(field_name="organization__id")
    ram_min = django_filters.NumberFilter(field_name="ram", lookup_expr="gte")
    ram_max = django_filters.NumberFilter(field_name="ram", lookup_expr="lte")
    storage_type = django_filters.ChoiceFilter(choices=Device.storage_type.field.choices)
    browser = django_filters.NumberFilter(field_name="browser__id")
    position = django_filters.NumberFilter(field_name="position__id")
    internet_speed = django_filters.ChoiceFilter(choices=Device.internet_speed.field.choices)

    has_google_account = django_filters.BooleanFilter(field_name="has_google_account")
    has_apple_account = django_filters.BooleanFilter(field_name="has_apple_account")
    has_microsoft_account = django_filters.BooleanFilter(field_name="has_microsoft_account")
    is_attested = django_filters.BooleanFilter(field_name="is_attested")
    work_with_text = django_filters.BooleanFilter(field_name="work_with_text")
    work_with_images = django_filters.BooleanFilter(field_name="work_with_images")
    create_presentations = django_filters.BooleanFilter(field_name="create_presentations")
    work_with_audio = django_filters.BooleanFilter(field_name="work_with_audio")
    work_with_video = django_filters.BooleanFilter(field_name="work_with_video")

    class Meta:
        model = Device
        fields = [
            "status",
            "device_type",
            "location",
            "organization",
            "storage_type",
            "browser",
            "position",
            "internet_speed",
            "has_google_account",
            "has_apple_account",
            "has_microsoft_account",
            "is_attested",
            "work_with_text",
            "work_with_images",
            "create_presentations",
            "work_with_audio",
            "work_with_video",
        ]
