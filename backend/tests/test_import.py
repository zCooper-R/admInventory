import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from apps.import_export.models import ImportLog, ImportStatus
from apps.import_export.services import process_excel_import
from apps.inventory.models import Browser, Device, InternetSpeed, Position
from apps.locations.models import Organization
from .factories import AdminUserFactory

HEADERS = [
    "№ п/п",
    "Наименование юридического лица",
    "Наименование ОС",
    "Инв. №",
    "Наименование процессора",
    "Тактовая частота",
    "Оперативная память",
    "Тип диска",
    "Емкость диска",
    "Браузер которым пользуетесь",
    "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft",
    "Скорость интернета",
    "Провайдер",
    "Аттестованный компьютер",
    "Работа с текстом",
    "Работа с картинками, фотографиями",
    "Создание презентаций",
    "Работа с аудио",
    "Работа с видео",
    "Фамилия, инициалы сотрудника",
    "Должность",
]


def make_excel_bytes(rows: list[dict], include_numbering_row: bool = True) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(HEADERS)
    if include_numbering_row:
        ws.append([str(i) for i in range(1, len(HEADERS) + 1)])

    for idx, row in enumerate(rows, start=1):
        ws.append([
            row.get("№ п/п", str(idx)),
            row.get("Наименование юридического лица", ""),
            row.get("Наименование ОС", ""),
            row.get("Инв. №", ""),
            row.get("Наименование процессора", ""),
            row.get("Тактовая частота", ""),
            row.get("Оперативная память", ""),
            row.get("Тип диска", ""),
            row.get("Емкость диска", ""),
            row.get("Браузер которым пользуетесь", ""),
            row.get("Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft", ""),
            row.get("Скорость интернета", ""),
            row.get("Провайдер", ""),
            row.get("Аттестованный компьютер", ""),
            row.get("Работа с текстом", ""),
            row.get("Работа с картинками, фотографиями", ""),
            row.get("Создание презентаций", ""),
            row.get("Работа с аудио", ""),
            row.get("Работа с видео", ""),
            row.get("Фамилия, инициалы сотрудника", ""),
            row.get("Должность", ""),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def base_row(**overrides):
    payload = {
        "Наименование юридического лица": "МКУ ГИМК",
        "Наименование ОС": "Windows 10",
        "Инв. №": "INV-001",
        "Наименование процессора": "Intel Core i5",
        "Тактовая частота": "3.40",
        "Оперативная память": "16",
        "Тип диска": "SSD",
        "Емкость диска": "512",
        "Браузер которым пользуетесь": "Яндекс Браузер",
        "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft": "Аккаунт Google, Аккаунт Microsoft",
        "Скорость интернета": "Свыше 100 Мб/с",
        "Провайдер": "Ростелеком",
        "Аттестованный компьютер": "Да",
        "Работа с текстом": "Да",
        "Работа с картинками, фотографиями": "Да",
        "Создание презентаций": "Да",
        "Работа с аудио": "Нет",
        "Работа с видео": "Нет",
        "Фамилия, инициалы сотрудника": "Иванов И.И.",
        "Должность": "Специалист",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestExcelImportService:
    def _create_import_log(self, excel_bytes: bytes, filename: str = "test.xlsx") -> ImportLog:
        user = AdminUserFactory()
        uploaded = SimpleUploadedFile(
            filename,
            excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return ImportLog.objects.create(file=uploaded, uploaded_by=user)

    def test_import_creates_organization_position_browser_and_device(self):
        log = self._create_import_log(make_excel_bytes([base_row()]))

        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        assert log.created_count == 1
        assert Organization.objects.count() == 1
        assert Position.objects.count() == 1
        assert Browser.objects.count() == 1
        device = Device.objects.get(inventory_number="INV-001")
        assert device.organization.name == "МКУ ГИМК"
        assert device.position.name == "Специалист"
        assert device.browser.name == "Яндекс Браузер"

    def test_reimport_same_inventory_updates_device(self):
        first = base_row(**{"Инв. №": "INV-UPDATE", "Оперативная память": "8"})
        second = base_row(**{"Инв. №": "INV-UPDATE", "Оперативная память": "32", "Наименование ОС": "Windows 11"})

        log1 = self._create_import_log(make_excel_bytes([first]))
        process_excel_import(log1)

        log2 = self._create_import_log(make_excel_bytes([second]))
        process_excel_import(log2)
        log2.refresh_from_db()

        assert log2.updated_count == 1
        device = Device.objects.get(inventory_number="INV-UPDATE")
        assert device.ram == 32
        assert device.os == "Windows 11"

    def test_empty_inventory_number_is_row_error(self):
        log = self._create_import_log(make_excel_bytes([base_row(**{"Инв. №": ""})]))

        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.FAILED
        assert log.error_count == 1
        assert "инвентарный номер" in log.errors[0]["message"].lower()

    def test_empty_optional_fields_do_not_break_import(self):
        row = base_row(**{
            "Наименование процессора": "",
            "Тактовая частота": "",
            "Емкость диска": "",
            "Браузер которым пользуетесь": "",
            "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft": "",
            "Провайдер": "",
            "Фамилия, инициалы сотрудника": "",
            "Должность": "",
        })
        log = self._create_import_log(make_excel_bytes([row]))

        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        device = Device.objects.get(inventory_number="INV-001")
        assert device.browser is None
        assert device.position is None
        assert device.has_google_account is None

    def test_organization_normalization_merges_aliases(self):
        row1 = base_row(**{"Инв. №": "INV-ORG-1", "Наименование юридического лица": "МКУ ГИМК"})
        row2 = base_row(**{
            "Инв. №": "INV-ORG-2",
            "Наименование юридического лица": "Муниципальное казенное учреждение Городской информационно-методический кабинет",
        })

        log = self._create_import_log(make_excel_bytes([row1, row2]))
        process_excel_import(log)

        assert Organization.objects.count() == 1
        org = Organization.objects.first()
        assert org.normalized_name == "мку гимк"

    def test_accounts_field_is_split_into_three_flags(self):
        row = base_row(**{
            "Инв. №": "INV-ACC-1",
            "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft": "Аккаунт Google, Аккаунт Apple",
        })
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-ACC-1")
        assert device.has_google_account is True
        assert device.has_apple_account is True
        assert device.has_microsoft_account is False

    def test_bool_fields_are_parsed(self):
        row = base_row(**{
            "Инв. №": "INV-BOOL-1",
            "Аттестованный компьютер": "+",
            "Работа с текстом": "да",
            "Работа с картинками, фотографиями": "есть",
            "Создание презентаций": "true",
            "Работа с аудио": "-",
            "Работа с видео": "нет",
        })
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-BOOL-1")
        assert device.is_attested is True
        assert device.work_with_text is True
        assert device.work_with_images is True
        assert device.create_presentations is True
        assert device.work_with_audio is False
        assert device.work_with_video is False

    def test_internet_speed_maps_to_choice_value(self):
        row = base_row(**{"Инв. №": "INV-NET-1", "Скорость интернета": "От 5 до 50 Мб/с"})
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-NET-1")
        assert device.internet_speed == InternetSpeed.FROM_5_TO_50

    def test_error_in_one_row_does_not_break_whole_import(self):
        bad_row = base_row(**{"Инв. №": "INV-BAD-1", "Тип диска": "NVME"})
        good_row = base_row(**{"Инв. №": "INV-GOOD-1"})

        log = self._create_import_log(make_excel_bytes([bad_row, good_row]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.PARTIAL
        assert log.error_count == 1
        assert Device.objects.filter(inventory_number="INV-GOOD-1").exists()
        assert not Device.objects.filter(inventory_number="INV-BAD-1").exists()
