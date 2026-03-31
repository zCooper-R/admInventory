from __future__ import annotations

from dataclasses import dataclass

from apps.inventory.models import Device, DeviceType, ReplacementStatus, SystemSettings


@dataclass(slots=True)
class LocationSummary:
    organization_name: str
    total_devices: int
    to_replace: int
    attention: int
    ok: int
    price_per_pc: int

    @property
    def estimated_cost(self) -> int:
        return self.to_replace * self.price_per_pc


@dataclass
class BudgetReport:
    devices: list[Device]
    by_organization: list[LocationSummary]
    price_per_pc: int

    @property
    def total_pcs(self) -> int:
        return len(self.devices)

    @property
    def replacement_count(self) -> int:
        return sum(1 for d in self.devices if d.replacement_status == ReplacementStatus.REPLACE)

    @property
    def attention_count(self) -> int:
        return sum(1 for d in self.devices if d.replacement_status == ReplacementStatus.ATTENTION)

    @property
    def ok_count(self) -> int:
        return sum(1 for d in self.devices if d.replacement_status == ReplacementStatus.OK)

    @property
    def total_cost(self) -> int:
        return self.replacement_count * self.price_per_pc


_BUDGET_CACHE_KEY = "budget_report_default"
_BUDGET_CACHE_TTL = 300


def build_budget_report(price_per_pc: int | None = None) -> BudgetReport:
    cfg = SystemSettings.get()
    effective_price = price_per_pc if price_per_pc is not None else cfg.pc_price_default

    devices = list(
        Device.objects.filter(device_type=DeviceType.PC)
        .select_related("organization", "position", "browser")
        .order_by("organization__name", "inventory_number")
    )

    grouped: dict[int, dict] = {}
    for d in devices:
        oid = d.organization_id
        if oid not in grouped:
            grouped[oid] = {
                "organization_name": d.organization.name,
                "total": 0,
                "replace": 0,
                "attention": 0,
                "ok": 0,
            }
        group = grouped[oid]
        group["total"] += 1
        if d.replacement_status == ReplacementStatus.REPLACE:
            group["replace"] += 1
        elif d.replacement_status == ReplacementStatus.ATTENTION:
            group["attention"] += 1
        else:
            group["ok"] += 1

    by_organization = [
        LocationSummary(
            organization_name=v["organization_name"],
            total_devices=v["total"],
            to_replace=v["replace"],
            attention=v["attention"],
            ok=v["ok"],
            price_per_pc=effective_price,
        )
        for v in grouped.values()
    ]
    by_organization.sort(key=lambda item: (-item.to_replace, item.organization_name))

    return BudgetReport(devices=devices, by_organization=by_organization, price_per_pc=effective_price)


def get_cached_budget_report() -> BudgetReport:
    from django.core.cache import cache

    return cache.get_or_set(_BUDGET_CACHE_KEY, build_budget_report, _BUDGET_CACHE_TTL)


def invalidate_budget_cache() -> None:
    from django.core.cache import cache

    cache.delete(_BUDGET_CACHE_KEY)
