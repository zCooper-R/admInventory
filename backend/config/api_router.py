from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.locations.views import OrganizationViewSet, LocationViewSet
from apps.inventory.api_views import DeviceViewSet

router = DefaultRouter()
router.register(r"devices", DeviceViewSet, basename="device")
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"locations", LocationViewSet, basename="location")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]
