import pytest
from django.test import Client
from django.urls import reverse

from apps.inventory.models import ReplacementStatus
from .factories import AdminUserFactory, DeviceFactory, OrganizationFactory


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
        r2 = client_auth.post(reverse("pc-edit", kwargs={"pk": device.pk}), edit_payload)
        assert r2.status_code == 302

        r3 = client_auth.post(reverse("pc-delete", kwargs={"pk": device.pk}))
        assert r3.status_code == 302
