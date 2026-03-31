import io

import pandas as pd
import pytest

from apps.import_export.models import ImportLog, ImportStatus
from apps.import_export.services import process_excel_import
from apps.inventory.models import Browser, Device, InternetSpeed, Position, StorageType
from apps.locations.models import Organization
from .factories import AdminUserFactory


NEW_COLUMNS = {
    "Наименование юридического лица": "МКУ ГИМК",
    "Наименование ОС": "Windows 10 Pro",
    "Инв. №": "TEST-INV-001",
    "Наименование процессора": "Intel Core i5-12400",
    "Тактовая частота": 2.5,
    "Оперативная память": 16,
    "Тип диска": "SSD",
    "Емкость диска": 512,
    "Браузер которым пользуетесь": "Яндекс Браузер",
    "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft": "Аккаунт Google",
    "Скорость интернета": "Свыше 100 Мб/с",
    "Провайдер": "ПАО Ростелеком",
    "Аттестованный компьютер": "Да",
    "Работа с текстом": "Да",
    "Работа с картинками, фотографиями": "Да",
    "Создание презентаций": "Да",
    "Работа с аудио": "Нет",
    "Работа с видео": "Нет",
    "Фамилия, инициалы сотрудника": "Иванов И.И.",
    "Должность": "ведущий специалист",
}


def make_excel_bytes(data: list[dict]) -> bytes:
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Таблица данных")
    buf.seek(0)
    return buf.read()


def make_excel_with_numbering_row(data: list[dict]) -> bytes:
    df = pd.DataFrame(data)
    numbering = {col: i + 1 for i, col in enumerate(df.columns)}
    df = pd.concat([pd.DataFrame([numbering]), df], ignore_index=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Таблица данных")
    buf.seek(0)
    return buf.read()


@pytest.mark.django_db
class TestExcelImportService:
    def _create_import_log(self, excel_bytes: bytes, filename: str = "test.xlsx") -> ImportLog:
        from django.core.files.uploadedfile import SimpleUploadedFile

        user = AdminUserFactory()
        uploaded = SimpleUploadedFile(filename, excel_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        log = ImportLog.objects.create(file=uploaded, uploaded_by=user)
        return log

    def test_import_creates_device_and_reference_data(self):
        rows = [dict(NEW_COLUMNS)]
        log = self._create_import_log(make_excel_bytes(rows))

        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        assert log.created_count == 1

        device = Device.objects.get(inventory_number="TEST-INV-001")
        assert device.organization.name == "МКУ ГИМК"
        assert device.position.name == "ведущий специалист"
        assert device.browser.name == "Яндекс Браузер"
        assert device.storage_type == StorageType.SSD

    def test_import_updates_existing_by_inventory_number(self):
        org = Organization.objects.create(name="МКУ ГИМК")
        device = Device.objects.create(
            name="Устройство TEST-INV-001",
            inventory_number="TEST-INV-001",
            organization=org,
            os="Windows 10",
            ram=8,
            storage_type=StorageType.HDD,
        )

        row = dict(NEW_COLUMNS)
        row["Оперативная память"] = 32
        row["Тип диска"] = "SSD"

        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device.refresh_from_db()
        assert log.updated_count == 1
        assert device.ram == 32
        assert device.storage_type == StorageType.SSD

    def test_empty_inventory_number_is_row_error(self):
        row = dict(NEW_COLUMNS)
        row["Инв. №"] = ""

        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.FAILED
        assert log.error_count == 1

    def test_optional_fields_can_be_empty(self):
        row = {
            "Наименование юридического лица": "МКУ ГИМК",
            "Наименование ОС": "Windows 10 Pro",
            "Инв. №": "TEST-INV-EMPTY-01",
            "Оперативная память": 8,
            "Тип диска": "HDD",
        }

        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        device = Device.objects.get(inventory_number="TEST-INV-EMPTY-01")
        assert device.browser is None
        assert device.position is None

    def test_organization_normalization_merges_aliases(self):
        row1 = dict(NEW_COLUMNS)
        row1["Инв. №"] = "TEST-ORG-1"
        row1["Наименование юридического лица"] = "МКУ ГИМК"

        row2 = dict(NEW_COLUMNS)
        row2["Инв. №"] = "TEST-ORG-2"
        row2["Наименование юридического лица"] = "Муниципальное казенное учреждение ГИМК"

        log = self._create_import_log(make_excel_bytes([row1, row2]))
        process_excel_import(log)

        assert Organization.objects.count() == 1

    def test_accounts_field_is_split_into_three_flags(self):
        row = dict(NEW_COLUMNS)
        row["Инв. №"] = "TEST-ACC-1"
        row["Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft"] = "Аккаунт Google, Аккаунт Microsoft"

        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="TEST-ACC-1")
        assert device.has_google_account is True
        assert device.has_apple_account is False
        assert device.has_microsoft_account is True

    def test_boolean_values_are_parsed(self):
        row = dict(NEW_COLUMNS)
        row["Инв. №"] = "TEST-BOOL-1"
        row["Аттестованный компьютер"] = "+"
        row["Работа с текстом"] = "true"
        row["Работа с картинками, фотографиями"] = "нет"

        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="TEST-BOOL-1")
        assert device.is_attested is True
        assert device.uses_text is True
        assert device.uses_images is False

    def test_internet_speed_is_saved_from_choices(self):
        row = dict(NEW_COLUMNS)
        row["Инв. №"] = "TEST-NET-1"
        row["Скорость интернета"] = "От 50 до 100 Мб/с"

        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="TEST-NET-1")
        assert device.internet_speed == InternetSpeed.FROM_50_TO_100

    def test_row_error_does_not_break_whole_import(self):
        valid_row = dict(NEW_COLUMNS)
        valid_row["Инв. №"] = "TEST-PARTIAL-OK"

        invalid_row = dict(NEW_COLUMNS)
        invalid_row["Инв. №"] = "TEST-PARTIAL-BAD"
        invalid_row["Тип диска"] = "NVME"

        log = self._create_import_log(make_excel_with_numbering_row([valid_row, invalid_row]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.PARTIAL
        assert log.created_count == 1
        assert log.error_count == 1
        assert Device.objects.filter(inventory_number="TEST-PARTIAL-OK").exists()
        assert not Device.objects.filter(inventory_number="TEST-PARTIAL-BAD").exists()

    def test_service_numbering_row_is_skipped(self):
        row = dict(NEW_COLUMNS)
        row["Инв. №"] = "TEST-NUMROW-1"

        log = self._create_import_log(make_excel_with_numbering_row([row]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        assert log.created_count == 1
        assert log.total_rows == 1
        assert Device.objects.filter(inventory_number="TEST-NUMROW-1").exists()
