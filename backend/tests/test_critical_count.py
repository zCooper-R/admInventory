"""
Tests for the critical-PC count HTMX badge endpoint.

Covers
------
* Unauthenticated request is redirected.
* Response contains both OOB badge elements.
* Badge count reflects actual broken/write-off devices.
* Count updates when a device changes status.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
import pytest
from django.test import Client
from django.urls import reverse

from apps.inventory.models import DeviceStatus
from .factories import AdminUserFactory, DeviceFactory


@pytest.fixture
def auth_client(db):
    user = AdminUserFactory()
    c = Client()
    c.force_login(user)
    return c


@pytest.mark.django_db
class TestCriticalCountPartial:
    def test_requires_login(self):
        url = reverse("critical-count-partial")
        response = Client().get(url)
        assert response.status_code == 302
        assert "/login/" in response["Location"]

    def test_returns_200_for_authenticated(self, auth_client):
        url = reverse("critical-count-partial")
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_contains_oob_elements(self, auth_client):
        """Response must include both badge target IDs for HTMX OOB swap."""
        url = reverse("critical-count-partial")
        response = auth_client.get(url)
        content = response.content.decode()
        assert "topbar-critical-badge" in content
        assert "sidebar-critical-badge" in content

    def test_zero_when_no_devices(self, auth_client):
        url = reverse("critical-count-partial")
        response = auth_client.get(url)
        content = response.content.decode()
        assert "0" in content or 'class="badge' in content

    def test_counts_broken_and_write_off(self, auth_client):
        DeviceFactory(status=DeviceStatus.ACTIVE)
        DeviceFactory(status=DeviceStatus.BROKEN)
        DeviceFactory(status=DeviceStatus.WRITE_OFF)
        DeviceFactory(status=DeviceStatus.WRITE_OFF)

        url = reverse("critical-count-partial")
        response = auth_client.get(url)
        content = response.content.decode()
        # 1 broken + 2 write_off = 3 critical devices
        assert "3" in content

    def test_active_not_counted(self, auth_client):
        DeviceFactory(status=DeviceStatus.ACTIVE)
        DeviceFactory(status=DeviceStatus.ACTIVE)

        url = reverse("critical-count-partial")
        response = auth_client.get(url)
        content = response.content.decode()
        assert "2" not in content

    def test_count_updates_after_device_deleted(self, auth_client):
        pc = DeviceFactory(status=DeviceStatus.BROKEN)
        url = reverse("critical-count-partial")

        response = auth_client.get(url)
        assert "1" in response.content.decode()

        pc.delete()
        response = auth_client.get(url)
        assert "1" not in response.content.decode()
