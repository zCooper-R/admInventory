"""
Shared helpers for the Inventory web views.

These utilities are used across multiple view modules and are
imported here to avoid duplication.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

import json

from django.http import HttpResponse

from apps.inventory.models import Device, DeviceType


def is_htmx(request) -> bool:
    """Return ``True`` when the request carries the ``HX-Request: true`` header."""
    return request.headers.get("HX-Request") == "true"


def htmx_close_and_refresh(message: str, event: str = "pcSaved") -> HttpResponse:
    """
    Return an HTTP 204 response that instructs the HTMX client to:
    * show a toast notification with *message*,
    * close the currently open Bootstrap modal (``closeModal`` trigger),
    * refresh the PC table via the *event* trigger (``pcSaved`` / ``pcDeleted``).
    """
    response = HttpResponse(status=204)
    response["HX-Trigger"] = json.dumps(
        {event: {"message": message}, "closeModal": True}
    )
    return response


def pc_qs(user=None):
    """
    Base queryset for ``DeviceType.PC`` devices with all FK relations pre-fetched.

    Role-based scoping
    ------------------
    If *user* is a ``manager`` with a ``location_id`` set, the queryset is
    automatically filtered to that location only.  Superusers and admins
    see every PC regardless.
    """
    qs = Device.objects.filter(device_type=DeviceType.PC).select_related(
        "organization", "position", "browser", "location__organization", "assigned_to"
    )
    if (
        user
        and not user.is_superuser
        and getattr(user, "role", None) == "manager"
        and getattr(user, "location_id", None)
    ):
        qs = qs.filter(location_id=user.location_id)
    return qs
