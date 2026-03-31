"""
Inventory app forms.

Contains ModelForms and plain Forms for the PC web interface:

* ``PCForm``          — create / edit a PC device (HTMX modal)
* ``PCFilterForm``    — search & filter the PC list
* ``PCImportForm``    — upload an Excel file for bulk import
* ``SystemSettingsForm`` — edit operational system settings

Validation notes
----------------
* ``PCForm`` adds the Bootstrap ``is-invalid`` CSS class automatically to
  any field that has server-side errors, so ``invalid-feedback`` divs in
  the template are shown correctly after a failed HTMX POST.
* Client-side HTML5 validation is handled by adding ``required`` attributes
  and the ``needs-validation`` CSS class on the ``<form>`` element (see
  the modal partial template).

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from django import forms

from apps.inventory.models import Browser, Device, DeviceStatus, Position, StorageType, SystemSettings
from apps.locations.models import Location, Organization

_FC = "form-control"
_FS = "form-select"


# ── PC create / edit ──────────────────────────────────────────────────────────

class PCForm(forms.ModelForm):
    """
    ModelForm for creating and editing PC (``DeviceType.PC``) devices.

    The ``device_type`` field is intentionally excluded — it is always
    set to ``DeviceType.PC`` in the view before ``save()``.

    Bootstrap validation
    ~~~~~~~~~~~~~~~~~~~~
    After a failed submit the form re-renders inside the HTMX modal.
    ``__init__`` automatically appends ``is-invalid`` to every widget
    whose field has validation errors, so the template's
    ``<div class="invalid-feedback">`` blocks become visible.
    """

    browser_name = forms.CharField(
        required=False,
        label="Браузер",
        widget=forms.TextInput(attrs={"class": _FC, "list": "browser-suggestions", "placeholder": "Например: Яндекс Браузер"}),
    )
    position_name = forms.CharField(
        required=False,
        label="Должность",
        widget=forms.TextInput(attrs={"class": _FC, "list": "position-suggestions", "placeholder": "Например: ведущий специалист"}),
    )

    class Meta:
        model = Device
        fields = [
            "name",
            "inventory_number",
            "organization",
            "cpu",
            "ram",
            "storage_type",
            "storage_size",
            "os",
            "status",
            "location",
            "employee_name",
            "purchase_date",
            "serial_number",
        ]
        widgets = {
            "name":             forms.TextInput(attrs={"class": _FC, "placeholder": "ПК-Бухгалтерия", "required": True}),
            "inventory_number": forms.TextInput(attrs={"class": _FC, "placeholder": "INV-2024-001", "required": True}),
            "organization":     forms.Select(attrs={"class": _FS, "required": True}),
            "cpu":              forms.TextInput(attrs={"class": _FC, "placeholder": "Intel Core i5-12400 @ 2.50GHz"}),
            "ram":              forms.NumberInput(attrs={"class": _FC, "min": 1, "max": 4096, "placeholder": "16"}),
            "storage_type":     forms.Select(attrs={"class": _FS}),
            "storage_size":     forms.NumberInput(attrs={"class": _FC, "min": 1, "placeholder": "512"}),
            "os":               forms.TextInput(attrs={"class": _FC, "placeholder": "Windows 11 Pro 23H2"}),
            "status":           forms.Select(attrs={"class": _FS, "required": True}),
            "location":         forms.Select(attrs={"class": _FS}),
            "employee_name":    forms.TextInput(attrs={"class": _FC, "placeholder": "Иванов И.И."}),
            "purchase_date":    forms.DateInput(attrs={"class": _FC, "type": "date"}),
            "serial_number":    forms.TextInput(attrs={"class": _FC, "placeholder": "SN-XXXXXXXX"}),
        }
        help_texts = {
            "name": (
                "Понятное название ПК. Используйте схему, принятую в вашей организации, "
                "например: «ПК-Директор», «ПК-Кабинет-101»."
            ),
            "inventory_number": (
                "Уникальный инвентарный номер. Агент использует его для синхронизации; "
                "Excel-импорт обновляет запись по этому полю."
            ),
            "cpu": "Полное название процессора. Заполняется автоматически агентом.",
            "ram": "Объём оперативной памяти в ГБ. Ниже порога в настройках → критерий замены.",
            "storage_type": "HDD считается устаревшим и включается в отчёт замен.",
            "storage_size": "Объём накопителя в ГБ.",
            "os": "Операционная система. Заполняется автоматически агентом.",
            "status": (
                "«Активен» — работает штатно. "
                "«Сломан» / «Списан» — автоматически попадает в отчёт замен как критичный."
            ),
            "location": "Физическое место нахождения ПК (площадка / кабинет).",
            "assigned_to": "Пользователь, за которым закреплён ПК (необязательно).",
            "purchase_date": (
                "Реальная дата покупки устройства. "
                "Используется для расчёта возраста в отчёте замен. "
                "Заполняется агентом при первой синхронизации (если доступно)."
            ),
            "serial_number": (
                "Серийный номер с этикетки корпуса или коробки. "
                "Заполняется автоматически агентом."
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Extend default initialisation to:
        * make some fields optional,
        * limit querysets,
        * append ``is-invalid`` class to widgets with server-side errors.
        """
        super().__init__(*args, **kwargs)

        optional = ["cpu", "ram", "storage_size", "os", "location", "employee_name", "purchase_date", "serial_number"]
        for name in optional:
            self.fields[name].required = False

        self.fields["organization"].required = True
        self.fields["organization"].queryset = Organization.objects.order_by("name")
        self.fields["organization"].empty_label = "— Выберите организацию —"
        self.fields["location"].queryset = (
            Location.objects.select_related("organization").order_by("organization__name", "name")
        )
        self.fields["location"].empty_label = "— Не выбрана —"
        self.browser_suggestions = list(Browser.objects.order_by("name").values_list("name", flat=True))
        self.position_suggestions = list(Position.objects.order_by("name").values_list("name", flat=True))
        self.fields["browser_name"].initial = self.instance.browser.name if self.instance and self.instance.pk and self.instance.browser else ""
        self.fields["position_name"].initial = self.instance.position.name if self.instance and self.instance.pk and self.instance.position else ""

        # Append is-invalid to fields that have server-side errors
        # so Bootstrap's invalid-feedback divs become visible.
        for fname in self.errors:
            field = self.fields.get(fname)
            if field:
                existing = field.widget.attrs.get("class", "")
                if "is-invalid" not in existing:
                    field.widget.attrs["class"] = existing + " is-invalid"

    def save(self, commit=True):
        instance = super().save(commit=False)
        browser_name = (self.cleaned_data.get("browser_name") or "").strip()
        position_name = (self.cleaned_data.get("position_name") or "").strip()

        instance.browser = Browser.objects.get_or_create(name=browser_name)[0] if browser_name else None
        instance.position = Position.objects.get_or_create(name=position_name)[0] if position_name else None

        if commit:
            instance.save()
        return instance


# ── PC list filter ─────────────────────────────────────────────────────────────

class PCFilterForm(forms.Form):
    """
    Search and filter form for the PC list page.

    All fields are optional.  The view applies them progressively
    (AND logic): only non-empty fields narrow the queryset.
    """

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": _FC,
                "placeholder": "Имя, инв. номер, CPU, ОС...",
                "autocomplete": "off",
                "id": "id_search",
            }
        ),
        help_text="Поиск по нескольким полям одновременно.",
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Все статусы")] + list(DeviceStatus.choices),
        widget=forms.Select(attrs={"class": _FS}),
    )
    location = forms.ModelChoiceField(
        required=False,
        queryset=Location.objects.select_related("organization").order_by("organization__name", "name"),
        empty_label="Все площадки",
        widget=forms.Select(attrs={"class": _FS}),
    )
    organization = forms.ModelChoiceField(
        required=False,
        queryset=Organization.objects.order_by("name"),
        empty_label="Все организации",
        widget=forms.Select(attrs={"class": _FS}),
    )


# ── Excel import ──────────────────────────────────────────────────────────────

class PCImportForm(forms.Form):
    """File upload form for the Excel bulk-import page."""

    file = forms.FileField(
        label="Excel файл (.xlsx / .xls)",
        widget=forms.FileInput(
            attrs={
                "class": _FC,
                "accept": ".xlsx,.xls",
                "id": "id_file",
            }
        ),
        help_text=(
            "Целевой формат: лист «Таблица данных» из выгрузки организации. "
            "Обязательные колонки строки: Наименование юридического лица, Инв. №, "
            "Наименование ОС, Оперативная память, Тип диска. "
            "Записи обновляются по Инв. №."
        ),
    )


# ── System settings ───────────────────────────────────────────────────────────

class SystemSettingsForm(forms.ModelForm):
    """
    Form for editing the singleton ``SystemSettings`` record.

    Displayed on the /settings/ page.  Only administrator-role users
    should be able to reach this view.
    """

    class Meta:
        model = SystemSettings
        fields = [
            "system_title",
            "system_subtitle",
            "pc_min_ram_gb",
            "pc_max_age_years",
            "pc_price_default",
        ]
        widgets = {
            "system_title":     forms.TextInput(attrs={"class": _FC}),
            "system_subtitle":  forms.TextInput(attrs={"class": _FC}),
            "pc_min_ram_gb":    forms.NumberInput(attrs={"class": _FC, "min": 1, "max": 256}),
            "pc_max_age_years": forms.NumberInput(attrs={"class": _FC, "min": 1, "max": 30}),
            "pc_price_default": forms.NumberInput(attrs={"class": _FC, "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["system_subtitle"].required = False

        # Propagate is-invalid on validation errors
        for fname in self.errors:
            field = self.fields.get(fname)
            if field:
                existing = field.widget.attrs.get("class", "")
                if "is-invalid" not in existing:
                    field.widget.attrs["class"] = existing + " is-invalid"
