from apps.inventory.api_views import DeviceViewSet
from apps.locations.views import OrganizationViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"devices", DeviceViewSet, basename="device")
router.register(r"organizations", OrganizationViewSet, basename="organization")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]
