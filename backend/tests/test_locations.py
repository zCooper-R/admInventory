import pytest
from apps.locations.models import Organization
from rest_framework import status
from rest_framework.test import APIClient

from .factories import AdminUserFactory, OrganizationFactory


@pytest.fixture
def authenticated_client(db):
    user = AdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestOrganizationAPI:
    def test_create_organization(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/organizations/",
            {"name": "Тестовая Организация"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.filter(name="Тестовая Организация").exists()

    def test_list_organizations(self, authenticated_client):
        OrganizationFactory.create_batch(5)
        response = authenticated_client.get("/api/v1/organizations/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
