import pytest
from apps.inventory.models import ReplacementStatus
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from .factories import AdminUserFactory, DeviceFactory, OrganizationFactory, UserFactory


@pytest.fixture
def client_auth(db):
    c = Client()
    c.force_login(AdminUserFactory())
    return c


@pytest.mark.django_db
class TestWebViews:
    def test_dashboard(self, client_auth):
        DeviceFactory(replacement_status=ReplacementStatus.OK)
        response = client_auth.get(reverse("dashboard"))
        assert response.status_code == 200

    def test_pc_list_filters(self, client_auth):
        org = OrganizationFactory(name="МКУ Тест")
        DeviceFactory(organization=org, inventory_number="INV-1")
        DeviceFactory(inventory_number="INV-2")

        response = client_auth.get(reverse("pc-list"), {"organization": org.pk})
        assert response.status_code == 200
        page = response.context["pcs"]
        assert page.paginator.count == 1

    def test_create_edit_delete(self, client_auth):
        org = OrganizationFactory()
        create_payload = {
            "inventory_number": "WEB-001",
            "organization": org.pk,
            "os": "Windows 10",
            "ram": 16,
            "storage_type": "SSD",
            "employee_name": "Петров П.П.",
        }
        r1 = client_auth.post(reverse("pc-create"), create_payload)
        assert r1.status_code == 302

        device = DeviceFactory(inventory_number="WEB-EDIT", organization=org)
        edit_payload = {
            "inventory_number": "WEB-EDIT",
            "organization": org.pk,
            "os": "Windows 11",
            "ram": 32,
            "storage_type": "SSD",
            "employee_name": "Петров П.П.",
        }
        r2 = client_auth.post(
            reverse("pc-edit", kwargs={"pk": device.pk}), edit_payload
        )
        assert r2.status_code == 302

        r3 = client_auth.post(reverse("pc-delete", kwargs={"pk": device.pk}))
        assert r3.status_code == 302

    def test_sorting_by_new_fields(self, client_auth):
        org = OrganizationFactory(name="Орг С")
        DeviceFactory(
            inventory_number="S-1",
            organization=org,
            os="Windows 11",
            cpu_model="Intel Core i7-12700",
            cpu_frequency=3.8,
            ram=16,
            storage_type="SSD",
            storage_size=512,
            provider="Провайдер Б",
        )
        DeviceFactory(
            inventory_number="S-2",
            organization=org,
            os="Windows 10",
            cpu_model="Intel Core i3-7100",
            cpu_frequency=2.9,
            ram=8,
            storage_type="HDD",
            storage_size=256,
            provider="Провайдер А",
        )

        response = client_auth.get(
            reverse("pc-list"), {"sort": "cpu_frequency", "dir": "asc"}
        )
        assert response.status_code == 200
        page = response.context["pcs"]
        freqs = [float(item.cpu_frequency or 0) for item in page.object_list[:2]]
        assert freqs == sorted(freqs)

        response2 = client_auth.get(
            reverse("pc-list"), {"sort": "provider", "dir": "asc"}
        )
        assert response2.status_code == 200

    def test_russian_ui_labels_present(self, client_auth):
        response = client_auth.get(reverse("pc-list"))
        assert response.status_code == 200
        body = response.content.decode("utf-8")
        assert "Статус замены" in body
        assert "Инв. номер" in body

    def test_pc_table_has_wide_layout_classes(self, client_auth):
        DeviceFactory()
        response = client_auth.get(reverse("pc-list"))
        assert response.status_code == 200
        body = response.content.decode("utf-8")
        assert "pc-table-wrap" in body
        assert "pc-data-table" in body
        assert "col-sticky-inv" in body
        assert "col-sticky-org" in body

    def test_pagination_has_clickable_and_disabled_cursor_classes(self, client_auth):
        DeviceFactory.create_batch(40)
        response = client_auth.get(reverse("pc-list"))
        assert response.status_code == 200
        body = response.content.decode("utf-8")
        assert "page-link-clickable" in body
        assert "page-link-disabled" in body

    def test_logs_view_access_for_admin(self, client_auth, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        log_file.write_text(
            "2026-04-01 10:00:00 | INFO     | apps.inventory.views | ok\n"
            "2026-04-01 10:01:00 | ERROR    | apps.inventory.views | fail\n",
            encoding="utf-8",
        )

        with override_settings(LOG_DIR=str(log_dir)):
            response = client_auth.get(
                reverse("logs-view"),
                {"file": "app.log", "level": "ERROR", "q": "fail", "lines": 100},
            )

        assert response.status_code == 200
        body = response.content.decode("utf-8")
        assert "Логи приложения" in body
        assert "ERROR" in body
        assert "fail" in body

    def test_logs_view_forbidden_for_non_admin(self, db):
        c = Client()
        c.force_login(UserFactory())
        response = c.get(reverse("logs-view"))
        assert response.status_code == 302
        assert response.url == reverse("dashboard")
