import pytest
from apps.inventory.models import Device, ReplacementStatus
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
        ok = DeviceFactory()
        repl1 = DeviceFactory()
        repl2 = DeviceFactory()
        Device.objects.filter(pk=ok.pk).update(replacement_status=ReplacementStatus.OK)
        Device.objects.filter(pk=repl1.pk).update(
            replacement_status=ReplacementStatus.REPLACE
        )
        Device.objects.filter(pk=repl2.pk).update(
            replacement_status=ReplacementStatus.REPLACE
        )

        response = auth_client.get(reverse("critical-count-partial"))
        assert response.status_code == 200
        assert "2" in response.content.decode()
