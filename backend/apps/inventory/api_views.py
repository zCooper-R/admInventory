import hmac
import logging
from datetime import date

from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.inventory.filters import DeviceFilter
from apps.inventory.models import Device, DeviceType
from apps.inventory.serializers import DeviceDetailSerializer, DeviceListSerializer
from apps.locations.models import Organization

logger = logging.getLogger(__name__)


def _verify_agent_key(request) -> bool:
    expected = getattr(settings, "AGENT_API_KEY", "")
    if not expected:
        return False
    provided = request.headers.get("X-Api-Key") or request.GET.get("api_key", "")
    return hmac.compare_digest(provided, expected)


class DeviceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_class = DeviceFilter
    search_fields = [
        "inventory_number",
        "employee_name",
        "organization__name",
        "position__name",
        "browser__name",
        "cpu_model",
        "os",
    ]
    ordering_fields = [
        "inventory_number",
        "replacement_status",
        "replacement_score",
        "updated_at",
        "created_at",
    ]
    ordering = ["inventory_number"]

    def get_queryset(self):
        return Device.objects.select_related(
            "organization", "position", "browser"
        ).all()

    def get_serializer_class(self):
        if self.action == "list":
            return DeviceListSerializer
        return DeviceDetailSerializer

    @action(
        detail=False, methods=["post"], url_path="sync", permission_classes=[AllowAny]
    )
    def sync(self, request):
        if not _verify_agent_key(request):
            return Response(
                {"error": "Invalid or missing X-Api-Key header."},
                status=status.HTTP_403_FORBIDDEN,
            )

        inv_number = (request.data.get("inventory_number") or "").strip()
        if not inv_number:
            return Response(
                {"error": "inventory_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        defaults: dict = {
            "device_type": DeviceType.PC,
            "agent_hostname": (request.data.get("hostname") or "").strip(),
            "last_sync": timezone.now(),
        }

        for field in ("cpu_model", "os", "serial_number", "provider", "employee_name"):
            val = request.data.get(field)
            if val is not None:
                defaults[field] = str(val).strip()

        for int_field in ("ram", "storage_size"):
            val = request.data.get(int_field)
            if val is not None:
                try:
                    defaults[int_field] = int(val)
                except (TypeError, ValueError):
                    pass

        storage_type = request.data.get("storage_type")
        if storage_type in ("HDD", "SSD"):
            defaults["storage_type"] = storage_type

        organization_id = request.data.get("organization_id")
        if organization_id:
            org = Organization.objects.filter(pk=organization_id).first()
            if org:
                defaults["organization"] = org

        purchase_date_str = request.data.get("purchase_date")

        if not defaults.get("organization"):
            existing = Device.objects.filter(inventory_number=inv_number).first()
            if not existing:
                return Response(
                    {"error": "organization_id is required for new devices."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        device, created = Device.objects.update_or_create(
            inventory_number=inv_number, defaults=defaults
        )

        if created and purchase_date_str:
            try:
                device.purchase_date = date.fromisoformat(purchase_date_str)
                device.save(
                    update_fields=[
                        "purchase_date",
                        "replacement_status",
                        "replacement_score",
                        "replacement_reason",
                    ]
                )
            except ValueError:
                pass

        serializer = DeviceDetailSerializer(device)
        return Response(
            {"created": created, "device": serializer.data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
