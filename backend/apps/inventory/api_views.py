"""
DRF ViewSets for the Inventory REST API.

Endpoints
---------
GET/POST   /api/v1/devices/         — list & create devices
GET/PUT/DELETE /api/v1/devices/<pk>/ — retrieve, update, destroy
POST       /api/v1/devices/sync/    — agent upsert (X-Api-Key auth)

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
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

logger = logging.getLogger(__name__)


def _verify_agent_key(request) -> bool:
    """
    Verify the ``X-Api-Key`` header against ``settings.AGENT_API_KEY``.

    Uses :func:`hmac.compare_digest` for a constant-time comparison,
    protecting against timing side-channel attacks.
    """
    expected = getattr(settings, "AGENT_API_KEY", "")
    if not expected:
        return False
    provided = request.headers.get("X-Api-Key") or request.GET.get("api_key", "")
    return hmac.compare_digest(provided, expected)


class DeviceViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for :class:`~apps.inventory.models.Device`.

    Supports filtering by ``location``, ``status``, ``device_type``;
    full-text search across name, inventory_number, cpu, os, location.
    """

    permission_classes = [IsAuthenticated]
    filterset_class    = DeviceFilter
    search_fields      = ["name", "inventory_number", "cpu", "os", "location__name"]
    ordering_fields    = [
        "name", "inventory_number", "device_type", "status", "created_at", "updated_at",
    ]
    ordering = ["inventory_number"]

    def get_queryset(self):
        return Device.objects.select_related("location__organization", "assigned_to").all()

    def get_serializer_class(self):
        if self.action == "list":
            return DeviceListSerializer
        return DeviceDetailSerializer

    # ── Agent sync endpoint ────────────────────────────────────────────────────

    @action(
        detail=False,
        methods=["post"],
        url_path="sync",
        permission_classes=[AllowAny],
    )
    def sync(self, request):
        """
        POST /api/v1/devices/sync/

        Agent endpoint: create or update a PC record identified by
        ``inventory_number``.  Requires ``X-Api-Key`` header matching
        ``settings.AGENT_API_KEY``.

        Request body (JSON)
        -------------------
        inventory_number  str  required
        name              str  optional  (defaults to inventory_number)
        cpu               str  optional
        ram               int  optional  (GB)
        os                str  optional
        storage_type      str  optional  (HDD | SSD | Mixed)
        storage_size      int  optional  (GB)
        serial_number     str  optional
        purchase_date     str  optional  (ISO 8601: YYYY-MM-DD)
        location_id       int  optional  (FK → Location)
        """
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
            "device_type":    DeviceType.PC,
            "name":           (request.data.get("name") or inv_number).strip(),
            "agent_hostname": (request.data.get("hostname") or "").strip(),
            "last_sync":      timezone.now(),
        }

        for field in ("cpu", "os", "serial_number"):
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
        if storage_type in ("HDD", "SSD", "Mixed", "None"):
            defaults["storage_type"] = storage_type

        location_id = request.data.get("location_id")
        if location_id:
            defaults["location_id"] = location_id

        # purchase_date is only applied on initial creation to avoid
        # overwriting values that were set manually via the web UI.
        purchase_date_str = request.data.get("purchase_date")

        device, created = Device.objects.update_or_create(
            inventory_number=inv_number,
            defaults=defaults,
        )

        if created and purchase_date_str:
            try:
                device.purchase_date = date.fromisoformat(purchase_date_str)
                device.save(update_fields=["purchase_date"])
            except ValueError:
                pass

        logger.info(
            "Agent sync: %s device %s [%s]",
            "created" if created else "updated",
            inv_number,
            request.data.get("hostname", ""),
        )

        serializer = DeviceDetailSerializer(device)
        return Response(
            {"created": created, "device": serializer.data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
