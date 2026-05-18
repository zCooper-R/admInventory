from __future__ import annotations

from dataclasses import dataclass

from apps.inventory.models import Device, DeviceType, ReplacementStatus, SystemSettings
from django.db.models import Count, Q

DEFAULT_PC_PRICE_FALLBACK = 60_000


@dataclass(frozen=True)
class OrganizationBudgetReportRow:
    organization_name: str
    total_devices: int
    bad_devices: int
    required_money: int


def resolve_pc_price(raw_price: str | int | None = None) -> int:
    if raw_price not in (None, ""):
        try:
            price = int(raw_price)
        except (TypeError, ValueError):
            price = 0
        if price > 0:
            return price

    try:
        settings = SystemSettings.get()
        if settings.pc_price_default > 0:
            return int(settings.pc_price_default)
    except Exception:
        pass

    return DEFAULT_PC_PRICE_FALLBACK


def build_organization_budget_report_rows(
    price: int,
) -> list[OrganizationBudgetReportRow]:
    rows = (
        Device.objects.filter(device_type=DeviceType.PC)
        .values("organization__name")
        .annotate(
            total_devices=Count("id"),
            bad_devices=Count(
                "id",
                filter=Q(replacement_status=ReplacementStatus.REPLACE),
            ),
        )
        .order_by("-bad_devices", "organization__name")
    )

    return [
        OrganizationBudgetReportRow(
            organization_name=row["organization__name"] or "",
            total_devices=row["total_devices"],
            bad_devices=row["bad_devices"],
            required_money=row["bad_devices"] * price,
        )
        for row in rows
    ]
