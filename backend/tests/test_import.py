import io
import pytest
import pandas as pd

from apps.inventory.models import Device, DeviceStatus
from apps.import_export.services import process_excel_import, ImportResult
from apps.import_export.models import ImportLog, ImportStatus
from .factories import AdminUserFactory, LocationFactory


def make_excel_bytes(data: list[dict]) -> bytes:
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
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

    def test_import_creates_devices(self):
        location = LocationFactory(name="Главный офис")
        rows = [
            {
                "name": "ПК-Тест-01",
                "inventory_number": "TEST-IMP-001",
                "device_type": "PC",
                "cpu": "Intel i5",
                "ram": 16,
                "storage_type": "SSD",
                "storage_size": 512,
                "os": "Windows 11",
                "status": "active",
                "location": "Главный офис",
                "assigned_to": "",
            }
        ]
        log = self._create_import_log(make_excel_bytes(rows))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.SUCCESS
        assert log.created_count == 1
        assert Device.objects.filter(inventory_number="TEST-IMP-001").exists()

    def test_import_updates_existing_device(self):
        location = LocationFactory(name="Офис Обновления")
        Device.objects.create(
            name="Старое имя",
            inventory_number="UPDATE-001",
            device_type="PC",
            status=DeviceStatus.ACTIVE,
            location=location,
        )
        rows = [
            {
                "name": "Новое имя",
                "inventory_number": "UPDATE-001",
                "device_type": "PC",
                "cpu": "AMD Ryzen 7",
                "ram": 32,
                "storage_type": "SSD",
                "storage_size": 1000,
                "os": "Ubuntu 22.04",
                "status": "active",
                "location": "Офис Обновления",
                "assigned_to": "",
            }
        ]
        log = self._create_import_log(make_excel_bytes(rows))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.updated_count == 1
        device = Device.objects.get(inventory_number="UPDATE-001")
        assert device.name == "Новое имя"
        assert device.ram == 32

    def test_import_fails_on_unknown_location(self):
        rows = [
            {
                "name": "ПК-Неизвестная-площадка",
                "inventory_number": "TEST-IMP-ERR-001",
                "device_type": "PC",
                "status": "active",
                "location": "Несуществующая площадка",
                "assigned_to": "",
            }
        ]
        log = self._create_import_log(make_excel_bytes(rows))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.FAILED
        assert log.error_count == 1

    def test_import_missing_required_column(self):
        rows = [{"device_type": "PC", "status": "active"}]
        log = self._create_import_log(make_excel_bytes(rows))
        process_excel_import(log)
        log.refresh_from_db()

        assert log.status == ImportStatus.FAILED
