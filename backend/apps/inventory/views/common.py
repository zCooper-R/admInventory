from __future__ import annotations

import json

from django.http import HttpResponse

from apps.inventory.models import Device, DeviceType


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def htmx_close_and_refresh(message: str, event: str = "pcSaved") -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Trigger"] = json.dumps({event: {"message": message}, "closeModal": True})
    return response


def pc_qs(user=None):
    qs = Device.objects.filter(device_type=DeviceType.PC).select_related("organization", "position", "browser")
    return qs
