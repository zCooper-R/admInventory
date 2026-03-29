"""Tests for web (Django-template) views and export service."""
import io
import pytest
from django.urls import reverse
from django.test import Client

from apps.inventory.models import Device, DeviceType, DeviceStatus
from apps.inventory.services.export import export_pcs_to_excel
from .factories import AdminUserFactory, DeviceFactory, LocationFactory


@pytest.fixture
def client_auth(db):
    user = AdminUserFactory()
    c = Client()
    c.force_login(user)
    return c


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestDashboard:
    def test_redirect_when_anonymous(self):
        response = Client().get(reverse("dashboard"))
        assert response.status_code == 302

    def test_loads_for_authenticated_user(self, client_auth):
        DeviceFactory.create_batch(3, device_type=DeviceType.PC)
        response = client_auth.get(reverse("dashboard"))
        assert response.status_code == 200

    def test_counts_only_pcs(self, client_auth):
        DeviceFactory(device_type=DeviceType.PC, status=DeviceStatus.ACTIVE)
        DeviceFactory(device_type=DeviceType.PC, status=DeviceStatus.BROKEN)
        DeviceFactory(device_type="Laptop")
        response = client_auth.get(reverse("dashboard"))
        assert response.context["total"] == 2
        assert response.context["active"] == 1
        assert response.context["broken"] == 1

    def test_context_has_chart_json(self, client_auth):
        response = client_auth.get(reverse("dashboard"))
        assert "status_chart_json" in response.context
        assert "location_chart_json" in response.context


# ═══════════════════════════════════════════════════════════════════════════════
# PC List
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestPCList:
    def test_shows_only_pcs(self, client_auth):
        DeviceFactory(device_type=DeviceType.PC)
        DeviceFactory(device_type="Laptop")
        response = client_auth.get(reverse("pc-list"))
        assert response.status_code == 200
        assert response.context["total_count"] == 1

    def test_filter_by_status(self, client_auth):
        DeviceFactory(device_type=DeviceType.PC, status=DeviceStatus.ACTIVE)
        DeviceFactory(device_type=DeviceType.PC, status=DeviceStatus.BROKEN)
        response = client_auth.get(reverse("pc-list") + "?status=broken")
        assert response.context["total_count"] == 1

    def test_filter_by_location(self, client_auth):
        loc = LocationFactory()
        DeviceFactory(device_type=DeviceType.PC, location=loc)
        DeviceFactory(device_type=DeviceType.PC)
        response = client_auth.get(reverse("pc-list") + f"?location={loc.pk}")
        assert response.context["total_count"] == 1

    def test_search_by_inventory_number(self, client_auth):
        DeviceFactory(device_type=DeviceType.PC, inventory_number="FIND-ME-001")
        DeviceFactory(device_type=DeviceType.PC, inventory_number="OTHER-999")
        response = client_auth.get(reverse("pc-list") + "?search=FIND-ME")
        assert response.context["total_count"] == 1

    def test_sort_by_name(self, client_auth):
        DeviceFactory(device_type=DeviceType.PC, name="Зебра")
        DeviceFactory(device_type=DeviceType.PC, name="Антилопа")
        response = client_auth.get(reverse("pc-list") + "?sort=name&dir=asc")
        names = [pc.name for pc in response.context["pcs"]]
        assert names == sorted(names)


# ═══════════════════════════════════════════════════════════════════════════════
# PC Create
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestPCCreate:
    def test_get_form(self, client_auth):
        response = client_auth.get(reverse("pc-create"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_creates_pc(self, client_auth):
        loc = LocationFactory()
        response = client_auth.post(reverse("pc-create"), {
            "name": "ПК-Тест",
            "inventory_number": "WEB-001",
            "status": "active",
            "storage_type": "SSD",
            "location": loc.pk,
        })
        assert response.status_code == 302
        pc = Device.objects.get(inventory_number="WEB-001")
        assert pc.device_type == DeviceType.PC

    def test_duplicate_inventory_number_fails(self, client_auth):
        existing = DeviceFactory(device_type=DeviceType.PC, inventory_number="DUP-001")
        loc = LocationFactory()
        response = client_auth.post(reverse("pc-create"), {
            "name": "Дубликат",
            "inventory_number": "DUP-001",
            "status": "active",
            "storage_type": "SSD",
            "location": loc.pk,
        })
        assert response.status_code == 200
        assert Device.objects.filter(inventory_number="DUP-001").count() == 1


# ═══════════════════════════════════════════════════════════════════════════════
# PC Edit
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestPCEdit:
    def test_get_edit_form(self, client_auth):
        pc = DeviceFactory(device_type=DeviceType.PC)
        response = client_auth.get(reverse("pc-edit", kwargs={"pk": pc.pk}))
        assert response.status_code == 200

    def test_post_updates_pc(self, client_auth):
        pc = DeviceFactory(device_type=DeviceType.PC, status=DeviceStatus.ACTIVE)
        response = client_auth.post(reverse("pc-edit", kwargs={"pk": pc.pk}), {
            "name": pc.name,
            "inventory_number": pc.inventory_number,
            "status": "broken",
            "storage_type": "SSD",
            "location": pc.location.pk,
        })
        assert response.status_code == 302
        pc.refresh_from_db()
        assert pc.status == DeviceStatus.BROKEN

    def test_404_for_non_pc(self, client_auth):
        laptop = DeviceFactory(device_type="Laptop")
        response = client_auth.get(reverse("pc-edit", kwargs={"pk": laptop.pk}))
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# PC Delete
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestPCDelete:
    def test_get_shows_confirm_page(self, client_auth):
        pc = DeviceFactory(device_type=DeviceType.PC)
        response = client_auth.get(reverse("pc-delete", kwargs={"pk": pc.pk}))
        assert response.status_code == 200
        assert response.context["pc"] == pc

    def test_post_deletes_pc(self, client_auth):
        pc = DeviceFactory(device_type=DeviceType.PC)
        pk = pc.pk
        response = client_auth.post(reverse("pc-delete", kwargs={"pk": pk}))
        assert response.status_code == 302
        assert not Device.objects.filter(pk=pk).exists()


# ═══════════════════════════════════════════════════════════════════════════════
# Export Service
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestExportService:
    def test_returns_bytes(self):
        DeviceFactory(device_type=DeviceType.PC)
        result = export_pcs_to_excel()
        assert isinstance(result, bytes)
        assert len(result) > 100

    def test_empty_export_still_works(self):
        result = export_pcs_to_excel()
        assert isinstance(result, bytes)

    def test_excludes_non_pcs(self):
        DeviceFactory(device_type=DeviceType.PC, inventory_number="PC-EXP-001")
        DeviceFactory(device_type="Laptop", inventory_number="LAP-EXP-001")
        excel_bytes = export_pcs_to_excel()

        import pandas as pd
        df = pd.read_excel(io.BytesIO(excel_bytes))
        assert len(df) == 1

    def test_export_view_returns_xlsx(self, client_auth):
        DeviceFactory(device_type=DeviceType.PC)
        response = client_auth.get(reverse("pc-export"))
        assert response.status_code == 200
        assert "spreadsheetml" in response["Content-Type"]
        assert "attachment" in response["Content-Disposition"]
