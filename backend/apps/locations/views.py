from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Location, Organization
from .serializers import LocationSerializer, OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.select_related("organization").all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["organization"]
    search_fields = ["name", "address", "organization__name"]
    ordering_fields = ["name", "organization__name", "created_at"]
    ordering = ["name"]
