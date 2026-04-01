from django import forms

from apps.inventory.models import (
    Browser,
    Device,
    InternetSpeed,
    Position,
    ReplacementStatus,
    StorageType,
    SystemSettings,
)
from apps.locations.models import Organization

_FC = "form-control"
_FS = "form-select"
_FCHK = "form-check-input"


class PCForm(forms.ModelForm):
    has_google_account = forms.BooleanField(
        label="Аккаунт Google",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    has_apple_account = forms.BooleanField(
        label="Аккаунт Apple",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    has_microsoft_account = forms.BooleanField(
        label="Аккаунт Microsoft",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    is_certified = forms.BooleanField(
        label="Аттестованный компьютер",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    use_for_text = forms.BooleanField(
        label="Работа с текстом",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    use_for_images = forms.BooleanField(
        label="Работа с картинками/фотографиями",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    use_for_presentations = forms.BooleanField(
        label="Создание презентаций",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    use_for_audio = forms.BooleanField(
        label="Работа с аудио",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )
    use_for_video = forms.BooleanField(
        label="Работа с видео",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": _FCHK}),
    )

    class Meta:
        model = Device
        fields = [
            "inventory_number",
            "organization",
            "employee_name",
            "position",
            "browser",
            "os",
            "cpu_model",
            "cpu_frequency",
            "ram",
            "storage_type",
            "storage_size",
            "internet_speed",
            "provider",
            "has_google_account",
            "has_apple_account",
            "has_microsoft_account",
            "is_certified",
            "use_for_text",
            "use_for_images",
            "use_for_presentations",
            "use_for_audio",
            "use_for_video",
            "purchase_date",
            "serial_number",
        ]
        widgets = {
            "inventory_number": forms.TextInput(attrs={"class": _FC, "required": True}),
            "organization": forms.Select(attrs={"class": _FS, "required": True}),
            "employee_name": forms.TextInput(attrs={"class": _FC}),
            "position": forms.Select(attrs={"class": _FS}),
            "browser": forms.Select(attrs={"class": _FS}),
            "os": forms.TextInput(attrs={"class": _FC, "required": True}),
            "cpu_model": forms.TextInput(attrs={"class": _FC}),
            "cpu_frequency": forms.NumberInput(
                attrs={"class": _FC, "step": "0.01", "min": 0}
            ),
            "ram": forms.NumberInput(attrs={"class": _FC, "min": 0, "required": True}),
            "storage_type": forms.Select(attrs={"class": _FS, "required": True}),
            "storage_size": forms.NumberInput(attrs={"class": _FC, "min": 0}),
            "internet_speed": forms.Select(attrs={"class": _FS}),
            "provider": forms.TextInput(attrs={"class": _FC}),
            "purchase_date": forms.DateInput(attrs={"class": _FC, "type": "date"}),
            "serial_number": forms.TextInput(attrs={"class": _FC}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organization"].queryset = Organization.objects.order_by("name")
        self.fields["position"].queryset = Position.objects.order_by("name")
        self.fields["browser"].queryset = Browser.objects.order_by("name")
        self.fields["position"].required = False
        self.fields["browser"].required = False
        self.fields["position"].empty_label = "— Не указана —"
        self.fields["browser"].empty_label = "— Не указан —"

        for field_name in self.errors:
            field = self.fields.get(field_name)
            if not field:
                continue
            css_class = field.widget.attrs.get("class", "")
            if "is-invalid" not in css_class:
                field.widget.attrs["class"] = (css_class + " is-invalid").strip()


class PCFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": _FC,
                "placeholder": "Инв.№ / сотрудник / организация",
                "autocomplete": "off",
                "id": "id_search",
            }
        ),
    )
    organization = forms.ModelChoiceField(
        required=False,
        queryset=Organization.objects.order_by("name"),
        empty_label="Все организации",
        widget=forms.Select(attrs={"class": _FS}),
    )
    position = forms.ModelChoiceField(
        required=False,
        queryset=Position.objects.order_by("name"),
        empty_label="Все должности",
        widget=forms.Select(attrs={"class": _FS}),
    )
    browser = forms.ModelChoiceField(
        required=False,
        queryset=Browser.objects.order_by("name"),
        empty_label="Все браузеры",
        widget=forms.Select(attrs={"class": _FS}),
    )
    replacement_status = forms.ChoiceField(
        required=False,
        choices=[("", "Все статусы")] + list(ReplacementStatus.choices),
        widget=forms.Select(attrs={"class": _FS}),
    )
    storage_type = forms.ChoiceField(
        required=False,
        choices=[("", "Все диски")] + list(StorageType.choices),
        widget=forms.Select(attrs={"class": _FS}),
    )
    internet_speed = forms.ChoiceField(
        required=False,
        choices=[("", "Любая скорость")] + list(InternetSpeed.choices),
        widget=forms.Select(attrs={"class": _FS}),
    )


class PCImportForm(forms.Form):
    file = forms.FileField(
        label="Excel файл (.xlsx / .xls)",
        widget=forms.FileInput(
            attrs={"class": _FC, "accept": ".xlsx,.xls", "id": "id_file"}
        ),
        help_text=(
            "Целевой формат нового импорта. Обязательные колонки в строке: "
            "Организация, Инв. №, Наименование ОС, Оперативная память, Тип диска."
        ),
    )


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            "system_title",
            "system_subtitle",
            "pc_min_ram_gb",
            "pc_max_age_years",
            "pc_price_default",
            "replacement_ram_low_threshold_gb",
            "replacement_ram_mid_threshold_gb",
            "replacement_ram_high_threshold_gb",
            "replacement_ram_low_score",
            "replacement_ram_mid_score",
            "replacement_ram_high_score",
            "replacement_ram_top_score",
            "replacement_storage_hdd_score",
            "replacement_storage_ssd_score",
            "replacement_cpu_weak_score",
            "replacement_cpu_medium_score",
            "replacement_cpu_good_score",
            "replacement_cpu_excellent_score",
            "replacement_cpu_unknown_score",
            "replacement_attention_threshold",
            "replacement_ok_threshold",
        ]
        widgets = {
            "system_title": forms.TextInput(attrs={"class": _FC}),
            "system_subtitle": forms.TextInput(attrs={"class": _FC}),
            "pc_min_ram_gb": forms.NumberInput(
                attrs={"class": _FC, "min": 1, "max": 256}
            ),
            "pc_max_age_years": forms.NumberInput(
                attrs={"class": _FC, "min": 1, "max": 30}
            ),
            "pc_price_default": forms.NumberInput(attrs={"class": _FC, "min": 1}),
            "replacement_ram_low_threshold_gb": forms.NumberInput(
                attrs={"class": _FC, "min": 1, "max": 1024}
            ),
            "replacement_ram_mid_threshold_gb": forms.NumberInput(
                attrs={"class": _FC, "min": 1, "max": 1024}
            ),
            "replacement_ram_high_threshold_gb": forms.NumberInput(
                attrs={"class": _FC, "min": 1, "max": 1024}
            ),
            "replacement_ram_low_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_ram_mid_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_ram_high_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_ram_top_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_storage_hdd_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_storage_ssd_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_cpu_weak_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_cpu_medium_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_cpu_good_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_cpu_excellent_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_cpu_unknown_score": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 100}
            ),
            "replacement_attention_threshold": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 300}
            ),
            "replacement_ok_threshold": forms.NumberInput(
                attrs={"class": _FC, "min": 0, "max": 300}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        low = cleaned.get("replacement_ram_low_threshold_gb")
        mid = cleaned.get("replacement_ram_mid_threshold_gb")
        high = cleaned.get("replacement_ram_high_threshold_gb")
        if None not in (low, mid, high) and not (low < mid < high):
            raise forms.ValidationError(
                "Пороги ОЗУ должны возрастать: низкий < средний < высокий."
            )

        attention = cleaned.get("replacement_attention_threshold")
        ok = cleaned.get("replacement_ok_threshold")
        if None not in (attention, ok) and not (attention < ok):
            raise forms.ValidationError(
                "Пороги статусов должны быть: внимание < норма."
            )
        return cleaned
