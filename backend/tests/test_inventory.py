import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.models import ReplacementStatus
from .factories import AdminUserFactory, DeviceFactory, OrganizationFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = AdminUserFactory()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestDeviceAPI:
    def test_list_devices(self, authenticated_client):
        DeviceFactory.create_batch(3)
        response = authenticated_client.get(reverse("device-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_filter_by_organization(self, authenticated_client):
        org = OrganizationFactory()
        DeviceFactory(organization=org)
        DeviceFactory()
        response = authenticated_client.get(
            reverse("device-list"), {"organization": org.pk}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_create_device_without_name_location_assigned_to(
        self, authenticated_client
    ):
        org = OrganizationFactory()
        payload = {
            "inventory_number": "NEW-001",
            "device_type": "PC",
            "organization": org.pk,
            "os": "Windows 11",
            "ram": 16,
            "storage_type": "SSD",
            "employee_name": "Иванов И.И.",
        }
        response = authenticated_client.post(
            reverse("device-list"), payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_replacement_status_is_present(self, authenticated_client):
        DeviceFactory(ram=4, storage_type="HDD")
        response = authenticated_client.get(reverse("device-list"))
        assert response.status_code == status.HTTP_200_OK
        item = response.data["results"][0]
        assert item["replacement_status"] in {
            ReplacementStatus.OK,
            ReplacementStatus.ATTENTION,
            ReplacementStatus.REPLACE,
        }
