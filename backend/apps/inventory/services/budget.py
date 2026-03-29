"""
Budget & replacement planning service.

Public API
----------
``build_budget_report(price_per_pc=None) -> BudgetReport``
    Analyse every PC in the database against the configurable health
    criteria and return a structured report that can be rendered by
    the budget template or consumed by other views.

``get_cached_budget_report() -> BudgetReport``
    Return the default-price report from the Django cache (TTL 5 min).
    Use this in views that do not accept a custom price parameter.

``invalidate_budget_cache() -> None``
    Delete the cached budget report.  Called automatically by the
    Device post-save / post-delete signals in ``apps.inventory.signals``.

How criteria are determined
---------------------------
Thresholds (minimum RAM, maximum age) are read from the singleton
``SystemSettings`` record at call time, so changes made on the
Settings page take effect immediately without a server restart.

Severity levels
---------------
critical  — device is broken or written off; must be replaced ASAP.
medium    — device is old or under-spec'd; plan replacement.
low       — mechanical HDD only; consider replacement.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from django.utils import timezone

from apps.inventory.models import Device, DeviceType, DeviceStatus

logger = logging.getLogger(__name__)

# Module-level fallback constants (used when SystemSettings cannot be read).
_DEFAULT_MIN_RAM_GB:    int = 8
_DEFAULT_MAX_AGE_YEARS: int = 4
_DEFAULT_PRICE:         int = 60_000

Severity = Literal["critical", "medium", "low"]
_SEV_ORDER: dict[Severity, int] = {"critical": 0, "medium": 1, "low": 2}


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass(slots=True)
class ReplacementReason:
    """A single reason why a PC should be replaced."""

    code: str
    """Machine-readable identifier (e.g. ``"low_ram"``)."""

    label: str
    """Human-readable description shown in the report table."""

    severity: Severity
    """One of ``"critical"``, ``"medium"``, or ``"low"``."""


@dataclass
class PCAssessment:
    """Assessment result for a single PC device."""

    pc: Device
    reasons: list[ReplacementReason] = field(default_factory=list)

    @property
    def needs_replacement(self) -> bool:
        """``True`` if the PC has at least one replacement reason."""
        return bool(self.reasons)

    @property
    def severity(self) -> Severity | None:
        """The most severe reason, or ``None`` if no issues found."""
        if not self.reasons:
            return None
        return min(self.reasons, key=lambda r: _SEV_ORDER[r.severity]).severity

    @property
    def severity_order(self) -> int:
        """Integer suitable for sorting (lower = more severe)."""
        return _SEV_ORDER.get(self.severity or "low", 99)

    @property
    def age_years(self) -> int | None:
        """Age in full years based on purchase_date (preferred) or created_at."""
        ref = self.pc.purchase_date or (self.pc.created_at.date() if self.pc.created_at else None)
        if not ref:
            return None
        return (timezone.now().date() - ref).days // 365


@dataclass
class LocationSummary:
    """Aggregated replacement statistics for one location."""

    location_name: str
    organization_name: str
    total_pcs: int
    to_replace: int
    critical_count: int
    price_per_pc: int

    @property
    def estimated_cost(self) -> int:
        """Estimated replacement cost = to_replace × price_per_pc."""
        return self.to_replace * self.price_per_pc

    @property
    def replacement_rate(self) -> int:
        """Percentage of PCs needing replacement (0–100)."""
        return round(self.to_replace / self.total_pcs * 100) if self.total_pcs else 0


@dataclass
class BudgetReport:
    """
    Full budget & replacement report for the entire PC fleet.

    Returned by :func:`build_budget_report`.  All properties are
    computed from ``assessments`` on the fly.
    """

    assessments: list[PCAssessment]
    """All PC assessments, sorted by severity then location."""

    by_location: list[LocationSummary]
    """Per-location summaries, sorted by critical count descending."""

    price_per_pc: int
    """Price used for cost calculations."""

    total_pcs: int
    """Total number of PC devices analysed."""

    @property
    def needing_replacement(self) -> list[PCAssessment]:
        """Subset of assessments where ``needs_replacement`` is ``True``."""
        return [a for a in self.assessments if a.needs_replacement]

    @property
    def replacement_count(self) -> int:
        return len(self.needing_replacement)

    @property
    def critical_count(self) -> int:
        return sum(1 for a in self.needing_replacement if a.severity == "critical")

    @property
    def medium_count(self) -> int:
        return sum(1 for a in self.needing_replacement if a.severity == "medium")

    @property
    def low_count(self) -> int:
        return sum(1 for a in self.needing_replacement if a.severity == "low")

    @property
    def total_cost(self) -> int:
        """Total estimated replacement cost."""
        return self.replacement_count * self.price_per_pc

    @property
    def replacement_rate(self) -> int:
        """Percentage of the fleet needing replacement (0–100)."""
        return round(self.replacement_count / self.total_pcs * 100) if self.total_pcs else 0

    @property
    def ok_count(self) -> int:
        """Number of PCs with no replacement reasons."""
        return self.total_pcs - self.replacement_count


# ── Internal assessment logic ──────────────────────────────────────────────────

def _assess(
    pc: Device,
    min_ram: int,
    max_age_years: int,
    today=None,
) -> PCAssessment:
    """
    Evaluate a single PC against the given thresholds.

    Parameters
    ----------
    pc:            Device instance (PC type).
    min_ram:       Minimum acceptable RAM in GB.
    max_age_years: Maximum acceptable age in years.
    today:         Pre-computed date to avoid N calls to ``timezone.now()``
                   when assessing many PCs in a loop.

    Returns
    -------
    PCAssessment with zero or more ReplacementReasons.
    """
    a = PCAssessment(pc=pc)
    if today is None:
        today = timezone.now().date()

    if pc.status == DeviceStatus.BROKEN:
        a.reasons.append(ReplacementReason("broken", "Сломан", "critical"))

    if pc.status == DeviceStatus.WRITE_OFF:
        a.reasons.append(ReplacementReason("write_off", "Списан", "critical"))

    if pc.ram is not None and pc.ram < min_ram:
        a.reasons.append(
            ReplacementReason(
                "low_ram",
                f"Мало ОЗУ ({pc.ram} ГБ, норма ≥ {min_ram} ГБ)",
                "medium",
            )
        )

    # Prefer explicit purchase_date; fall back to created_at as a proxy.
    ref_date = pc.purchase_date or (pc.created_at.date() if pc.created_at else None)
    if ref_date:
        age_days = (today - ref_date).days
        if age_days >= max_age_years * 365:
            age_y = age_days // 365
            note = "" if pc.purchase_date else " (по дате создания записи)"
            a.reasons.append(
                ReplacementReason(
                    "old_age",
                    f"Возраст {age_y} л.{note} (норма < {max_age_years} л.)",
                    "medium",
                )
            )

    if pc.storage_type == "HDD":
        a.reasons.append(ReplacementReason("no_ssd", "Механический диск (HDD)", "low"))

    return a


# ── Public API ─────────────────────────────────────────────────────────────────

def build_budget_report(price_per_pc: int | None = None) -> BudgetReport:
    """
    Assess every PC in the database and build a :class:`BudgetReport`.

    Thresholds and the default price are read from :class:`SystemSettings`
    at call time, so they always reflect the latest values saved on the
    Settings page.

    Parameters
    ----------
    price_per_pc:
        Override the default price (₽/unit) for cost calculations.
        If ``None``, the value from ``SystemSettings.pc_price_default`` is used.

    Returns
    -------
    BudgetReport
        Fully populated report object ready for template rendering.
    """
    from apps.inventory.models import SystemSettings
    cfg = SystemSettings.get()

    effective_price    = price_per_pc if price_per_pc is not None else cfg.pc_price_default
    effective_min_ram  = cfg.pc_min_ram_gb
    effective_max_age  = cfg.pc_max_age_years

    pcs = (
        Device.objects.filter(device_type=DeviceType.PC)
        .select_related("location__organization", "assigned_to")
        .order_by("location__organization__name", "location__name", "inventory_number")
    )

    today = timezone.now().date()  # compute once, not once-per-PC
    assessments = sorted(
        [_assess(pc, min_ram=effective_min_ram, max_age_years=effective_max_age, today=today) for pc in pcs],
        key=lambda a: (
            a.severity_order if a.needs_replacement else 99,
            a.pc.location.name if a.pc.location else "",
        ),
    )

    # Build per-location summaries
    loc_map: dict[int | None, dict] = {}
    for a in assessments:
        key = a.pc.location_id
        if key not in loc_map:
            loc_map[key] = {
                "location_name":     a.pc.location.name if a.pc.location else "Без площадки",
                "organization_name": (a.pc.location.organization.name if a.pc.location else ""),
                "total": 0,
                "to_replace": 0,
                "critical": 0,
            }
        d = loc_map[key]
        d["total"] += 1
        if a.needs_replacement:
            d["to_replace"] += 1
            if a.severity == "critical":
                d["critical"] += 1

    by_location = sorted(
        [
            LocationSummary(
                location_name=v["location_name"],
                organization_name=v["organization_name"],
                total_pcs=v["total"],
                to_replace=v["to_replace"],
                critical_count=v["critical"],
                price_per_pc=effective_price,
            )
            for v in loc_map.values()
            if v["to_replace"] > 0
        ],
        key=lambda ls: (-ls.critical_count, -ls.to_replace),
    )

    logger.info(
        "BudgetReport built: total=%d, to_replace=%d, critical=%d, cost=%d RUB (price=%d, min_ram=%d, max_age=%d)",
        len(assessments),
        sum(1 for a in assessments if a.needs_replacement),
        sum(1 for a in assessments if a.needs_replacement and a.severity == "critical"),
        sum(1 for a in assessments if a.needs_replacement) * effective_price,
        effective_price,
        effective_min_ram,
        effective_max_age,
    )

    return BudgetReport(
        assessments=assessments,
        by_location=by_location,
        price_per_pc=effective_price,
        total_pcs=len(assessments),
    )


# ── Cache helpers ──────────────────────────────────────────────────────────────

_BUDGET_CACHE_KEY = "budget_report_default"
_BUDGET_CACHE_TTL = 300  # seconds (5 minutes)


def get_cached_budget_report() -> BudgetReport:
    """
    Return the default-price budget report from the Django cache.

    On a cache miss the report is computed by :func:`build_budget_report`
    (with no custom price) and stored for :data:`_BUDGET_CACHE_TTL` seconds.

    The cache is invalidated automatically by the Device signals in
    ``apps.inventory.signals`` whenever a PC is saved or deleted.
    """
    from django.core.cache import cache

    return cache.get_or_set(_BUDGET_CACHE_KEY, build_budget_report, _BUDGET_CACHE_TTL)


def invalidate_budget_cache() -> None:
    """
    Evict the cached budget report.

    Should be called whenever PC data changes so the next request receives
    a fresh computation rather than stale numbers.
    """
    from django.core.cache import cache

    cache.delete(_BUDGET_CACHE_KEY)
    logger.debug("Budget cache invalidated.")
