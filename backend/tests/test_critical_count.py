import pytest
from apps.inventory.models import ReplacementStatus
from django.test import Client
from django.urls import reverse

from .factories import AdminUserFactory, DeviceFactory


@pytest.fixture
def auth_client(db):
    c = Client()
    c.force_login(AdminUserFactory())
    return c


@pytest.mark.django_db
class TestCriticalCountPartial:
    def test_counts_replace_status(self, auth_client):
        DeviceFactory(replacement_status=ReplacementStatus.OK)
        DeviceFactory(replacement_status=ReplacementStatus.REPLACE)
        DeviceFactory(replacement_status=ReplacementStatus.REPLACE)

        response = auth_client.get(reverse("critical-count-partial"))
        assert response.status_code == 200
        assert "2" in response.content.decode()
