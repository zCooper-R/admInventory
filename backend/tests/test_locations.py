import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.locations.models import Organization, Location
from .factories import AdminUserFactory, OrganizationFactory, LocationFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    user = AdminUserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestOrganizationAPI:
    def test_create_organization(self, authenticated_client):
        url = reverse("organization-list")
        response = authenticated_client.post(url, {"name": "Тестовая Организация"})
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.filter(name="Тестовая Организация").exists()

    def test_list_organizations(self, authenticated_client):
        OrganizationFactory.create_batch(5)
        url = reverse("organization-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5


@pytest.mark.django_db
class TestLocationAPI:
    def test_create_location(self, authenticated_client):
        org = OrganizationFactory()
        url = reverse("location-list")
        payload = {
            "name": "Тестовая площадка",
            "address": "г. Москва, ул. Тестовая, д. 1",
            "organization": org.pk,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_locations_by_organization(self, authenticated_client):
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        LocationFactory.create_batch(3, organization=org1)
        LocationFactory.create_batch(2, organization=org2)

        url = reverse("location-list")
        response = authenticated_client.get(url, {"organization": org1.pk})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
