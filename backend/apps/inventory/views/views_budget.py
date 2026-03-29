"""
Budget / replacement-planning view.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.inventory.services.budget import build_budget_report, get_cached_budget_report


@login_required
def budget_report(request):
    """
    Budget and replacement-planning report.

    Price logic
    -----------
    When ``?price=N`` is present in the URL the report is computed
    with that custom price (not cached — every user may have a different
    price in mind).  When the parameter is absent the cached default-price
    report is returned for speed.

    The JavaScript on the page calls ``history.replaceState`` whenever the
    price input changes, keeping the URL bookmarkable and shareable.
    """
    price_str = request.GET.get("price", "").strip()
    if price_str:
        try:
            price_per_pc = max(1, int(price_str))
        except (ValueError, TypeError):
            price_per_pc = None
        report = build_budget_report(price_per_pc)
    else:
        report = get_cached_budget_report()

    return render(request, "inventory/budget_report.html", {
        "nav_active":  "budget",
        "report":      report,
        "price_per_pc": report.price_per_pc,
    })
