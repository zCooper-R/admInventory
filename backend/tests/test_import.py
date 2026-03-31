import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from apps.import_export.models import ImportLog, ImportStatus
from apps.import_export.services import process_excel_import
from apps.inventory.models import Browser, Device, InternetSpeed, Position, ReplacementStatus
from apps.locations.models import Organization
from .factories import AdminUserFactory

HEADERS = [
    "№ п/п",
    "Наименование юридического лица",
    "Адрес организации",
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
            row.get("Адрес организации", ""),
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
        "Адрес организации": "ул. Тестовая, 1",
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
        uploaded = SimpleUploadedFile(filename, excel_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        return ImportLog.objects.create(file=uploaded, uploaded_by=user)

    def test_import_creates_device_and_dictionaries(self):
        log = self._create_import_log(make_excel_bytes([base_row()]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        assert Organization.objects.count() == 1
        assert Position.objects.count() == 1
        assert Browser.objects.count() == 1
        device = Device.objects.get(inventory_number="INV-001")
        assert device.organization.name == "МКУ ГИМК"
        assert device.organization.address == "ул. Тестовая, 1"
        assert device.employee_name == "Иванов И.И."

    def test_reimport_updates_by_inventory_number(self):
        log1 = self._create_import_log(make_excel_bytes([base_row(**{"Инв. №": "INV-UPDATE", "Оперативная память": "8"})]))
        process_excel_import(log1)

        log2 = self._create_import_log(make_excel_bytes([base_row(**{"Инв. №": "INV-UPDATE", "Оперативная память": "32"})]))
        process_excel_import(log2)

        device = Device.objects.get(inventory_number="INV-UPDATE")
        assert device.ram == 32

    def test_empty_inventory_number_is_row_error(self):
        log = self._create_import_log(make_excel_bytes([base_row(**{"Инв. №": ""})]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.error_count == 1
        assert "инвентарный номер" in log.errors[0]["message"].lower()

    def test_organization_normalization_merges_aliases(self):
        row1 = base_row(**{"Инв. №": "INV-ORG-1", "Наименование юридического лица": "МКУ ГИМК"})
        row2 = base_row(**{"Инв. №": "INV-ORG-2", "Наименование юридического лица": "Муниципальное казенное учреждение Городской информационно-методический кабинет"})
        log = self._create_import_log(make_excel_bytes([row1, row2]))
        process_excel_import(log)

        assert Organization.objects.count() == 1

    def test_accounts_field_is_split(self):
        row = base_row(**{"Инв. №": "INV-ACC", "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft": "Аккаунт Google, Аккаунт Apple"})
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-ACC")
        assert device.has_google_account is True
        assert device.has_apple_account is True
        assert device.has_microsoft_account is False

    def test_boolean_fields_parsing(self):
        row = base_row(**{
            "Инв. №": "INV-BOOL",
            "Аттестованный компьютер": "+",
            "Работа с текстом": "да",
            "Работа с картинками, фотографиями": "есть",
            "Создание презентаций": "true",
            "Работа с аудио": "-",
            "Работа с видео": "нет",
        })
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-BOOL")
        assert device.is_certified is True
        assert device.use_for_text is True
        assert device.use_for_images is True
        assert device.use_for_presentations is True
        assert device.use_for_audio is False
        assert device.use_for_video is False

    def test_internet_speed_choice(self):
        row = base_row(**{"Инв. №": "INV-NET", "Скорость интернета": "От 5 до 50 Мб/с"})
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-NET")
        assert device.internet_speed == InternetSpeed.FROM_5_TO_50

    def test_row_error_does_not_break_import(self):
        bad_row = base_row(**{"Инв. №": "INV-BAD", "Тип диска": "NVME"})
        good_row = base_row(**{"Инв. №": "INV-GOOD"})
        log = self._create_import_log(make_excel_bytes([bad_row, good_row]))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.PARTIAL
        assert Device.objects.filter(inventory_number="INV-GOOD").exists()
        assert not Device.objects.filter(inventory_number="INV-BAD").exists()

    def test_replacement_status_calculated(self):
        row = base_row(**{"Инв. №": "INV-REP", "Оперативная память": "4", "Тип диска": "HDD"})
        log = self._create_import_log(make_excel_bytes([row]))
        process_excel_import(log)

        device = Device.objects.get(inventory_number="INV-REP")
        assert device.replacement_status == ReplacementStatus.REPLACE
        assert device.replacement_score <= 2

    def test_tail_service_rows_are_skipped(self):
        wb = Workbook()
        ws = wb.active
        ws.append(HEADERS + ["Unnamed: 99"])
        ws.append([str(i) for i in range(1, len(HEADERS) + 2)])  # numbering row
        valid = base_row(**{"Инв. №": "INV-TAIL-1"})
        ws.append([valid.get(h, "") for h in HEADERS] + ["x"])
        ws.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "служебный хвост"])
        ws.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "итого: 1"])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        log = self._create_import_log(buf.read(), filename="tail.xlsx")
        process_excel_import(log)
        log.refresh_from_db()

        assert log.error_count == 0
        assert Device.objects.filter(inventory_number="INV-TAIL-1").exists()
        assert log.total_rows == 1

    def test_unnamed_columns_are_ignored_for_row_detection(self):
        wb = Workbook()
        ws = wb.active
        ws.append(HEADERS + ["Unnamed: 1", "Unnamed: 2"])
        ws.append([str(i) for i in range(1, len(HEADERS) + 3)])
        ws.append([""] * len(HEADERS) + ["служебно", "текст"])
        valid = base_row(**{"Инв. №": "INV-UNNAMED"})
        ws.append([valid.get(h, "") for h in HEADERS] + ["", ""])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        log = self._create_import_log(buf.read(), filename="unnamed.xlsx")
        process_excel_import(log)
        log.refresh_from_db()

        assert log.error_count == 0
        assert log.total_rows == 1
        assert Device.objects.filter(inventory_number="INV-UNNAMED").exists()
