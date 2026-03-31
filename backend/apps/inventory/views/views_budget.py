from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.inventory.services.budget import build_budget_report, get_cached_budget_report


@login_required
def budget_report(request):
    price_per_pc = request.GET.get("price")
    if price_per_pc:
        try:
            price_per_pc = int(price_per_pc)
        except ValueError:
            price_per_pc = None
    else:
        price_per_pc = None

    report = build_budget_report(price_per_pc) if price_per_pc else get_cached_budget_report()

    return render(
        request,
        "inventory/budget_report.html",
        {
            "nav_active": "budget",
            "report": report,
            "price_per_pc": report.price_per_pc,
        },
    )
