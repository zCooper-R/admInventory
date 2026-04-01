import django_filters

from .models import Device


class DeviceFilter(django_filters.FilterSet):
    organization = django_filters.NumberFilter(field_name="organization__id")
    position = django_filters.NumberFilter(field_name="position__id")
    browser = django_filters.NumberFilter(field_name="browser__id")

    replacement_status = django_filters.ChoiceFilter(
        choices=Device.replacement_status.field.choices
    )
    storage_type = django_filters.ChoiceFilter(
        choices=Device.storage_type.field.choices
    )
    internet_speed = django_filters.ChoiceFilter(
        choices=Device.internet_speed.field.choices
    )

    use_for_text = django_filters.BooleanFilter(field_name="use_for_text")
    use_for_images = django_filters.BooleanFilter(field_name="use_for_images")
    use_for_presentations = django_filters.BooleanFilter(
        field_name="use_for_presentations"
    )
    use_for_audio = django_filters.BooleanFilter(field_name="use_for_audio")
    use_for_video = django_filters.BooleanFilter(field_name="use_for_video")

    has_google_account = django_filters.BooleanFilter(field_name="has_google_account")
    has_apple_account = django_filters.BooleanFilter(field_name="has_apple_account")
    has_microsoft_account = django_filters.BooleanFilter(
        field_name="has_microsoft_account"
    )

    class Meta:
        model = Device
        fields = [
            "organization",
            "position",
            "browser",
            "replacement_status",
            "storage_type",
            "internet_speed",
            "use_for_text",
            "use_for_images",
            "use_for_presentations",
            "use_for_audio",
            "use_for_video",
            "has_google_account",
            "has_apple_account",
            "has_microsoft_account",
        ]
