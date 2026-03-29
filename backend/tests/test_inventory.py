import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.models import Device, DeviceStatus
from .factories import AdminUserFactory, DeviceFactory, LocationFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return AdminUserFactory()


@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.mark.django_db
class TestDeviceListAPI:
    def test_requires_authentication(self, api_client):
        url = reverse("device-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_devices(self, authenticated_client):
        DeviceFactory.create_batch(3)
        url = reverse("device-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_filter_by_status(self, authenticated_client):
        DeviceFactory(status=DeviceStatus.ACTIVE)
        DeviceFactory(status=DeviceStatus.BROKEN)
        DeviceFactory(status=DeviceStatus.WRITE_OFF)

        url = reverse("device-list")
        response = authenticated_client.get(url, {"status": "active"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_filter_by_location(self, authenticated_client):
        location = LocationFactory()
        DeviceFactory(location=location)
        DeviceFactory()  # different location

        url = reverse("device-list")
        response = authenticated_client.get(url, {"location": location.pk})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_search_by_inventory_number(self, authenticated_client):
        DeviceFactory(inventory_number="UNIQUE-9999")
        DeviceFactory(inventory_number="OTHER-0001")

        url = reverse("device-list")
        response = authenticated_client.get(url, {"search": "UNIQUE-9999"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestDeviceCRUD:
    def test_create_device(self, authenticated_client):
        location = LocationFactory()
        url = reverse("device-list")
        payload = {
            "name": "Тестовый ПК",
            "inventory_number": "TEST-0001",
            "device_type": "PC",
            "cpu": "Intel i5",
            "ram": 16,
            "storage_type": "SSD",
            "storage_size": 512,
            "os": "Windows 11",
            "status": "active",
            "location": location.pk,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Device.objects.filter(inventory_number="TEST-0001").exists()

    def test_update_device_status(self, authenticated_client):
        device = DeviceFactory(status=DeviceStatus.ACTIVE)
        url = reverse("device-detail", kwargs={"pk": device.pk})
        response = authenticated_client.patch(url, {"status": "broken"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        device.refresh_from_db()
        assert device.status == DeviceStatus.BROKEN

    def test_delete_device(self, authenticated_client):
        device = DeviceFactory()
        url = reverse("device-detail", kwargs={"pk": device.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Device.objects.filter(pk=device.pk).exists()

    def test_inventory_number_unique(self, authenticated_client):
        existing = DeviceFactory(inventory_number="DUP-001")
        location = LocationFactory()
        url = reverse("device-list")
        payload = {
            "name": "Дубликат",
            "inventory_number": existing.inventory_number,
            "device_type": "PC",
            "status": "active",
            "location": location.pk,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
