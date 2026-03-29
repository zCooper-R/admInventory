"""
PC CRUD views + Dashboard + critical-count badge partial.

Includes
--------
dashboard              — KPI cards, charts, budget alert widget
pc_list                — filterable/sortable table (HTMX partial-aware)
pc_create_modal        — HTMX modal: create PC
pc_edit_modal          — HTMX modal: edit PC
pc_delete_modal        — HTMX modal: delete PC
pc_create              — full-page fallback create
pc_edit                — full-page fallback edit
pc_delete              — full-page fallback delete
critical_count_partial — HTMX OOB badge refresh

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.inventory.forms import PCFilterForm, PCForm
from apps.inventory.models import Device, DeviceStatus, DeviceType
from apps.inventory.services.budget import get_cached_budget_report
from apps.inventory.views.common import htmx_close_and_refresh, is_htmx, pc_qs

_PAGE_SIZE = 25


# ── Dashboard ──────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    Main dashboard view.

    Computes PC fleet KPIs, prepares Chart.js data series, fetches the
    8 most-recently-updated PCs, and runs a cached budget analysis for
    the alert widget.
    """
    pcs   = pc_qs(request.user)
    total     = pcs.count()
    active    = pcs.filter(status=DeviceStatus.ACTIVE).count()
    broken    = pcs.filter(status=DeviceStatus.BROKEN).count()
    write_off = pcs.filter(status=DeviceStatus.WRITE_OFF).count()

    active_pct    = round(active    / total * 100) if total else 0
    broken_pct    = round(broken    / total * 100) if total else 0
    write_off_pct = 100 - active_pct - broken_pct  if total else 0

    status_chart = {
        "labels": ["Активен", "Сломан", "Списан"],
        "data":   [active, broken, write_off],
        "colors": ["#16a34a", "#d97706", "#dc2626"],
    }
    location_qs = (
        pcs.values("location__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:12]
    )
    location_chart = {
        "labels": [item["location__name"] or "Без площадки" for item in location_qs],
        "data":   [item["count"] for item in location_qs],
    }

    return render(request, "inventory/dashboard.html", {
        "nav_active":          "dashboard",
        "total":               total,
        "active":              active,
        "broken":              broken,
        "write_off":           write_off,
        "active_pct":          active_pct,
        "broken_pct":          broken_pct,
        "write_off_pct":       write_off_pct,
        "status_chart_json":   json.dumps(status_chart),
        "location_chart_json": json.dumps(location_chart),
        "recent_pcs":          pc_qs(request.user).order_by("-updated_at")[:8],
        "budget_report":       get_cached_budget_report(),
    })


# ── PC List ────────────────────────────────────────────────────────────────────

@login_required
def pc_list(request):
    """
    PC list with search, filtering, sorting, and HTMX-aware pagination.

    When the ``HX-Request`` header is present only the table partial
    (``inventory/_partials/pc_table.html``) is returned, avoiding a
    full-page reload.
    """
    qs   = pc_qs(request.user)
    form = PCFilterForm(request.GET)

    if form.is_valid():
        if s := form.cleaned_data.get("search"):
            qs = qs.filter(
                Q(name__icontains=s)
                | Q(inventory_number__icontains=s)
                | Q(cpu__icontains=s)
                | Q(os__icontains=s)
            )
        if status := form.cleaned_data.get("status"):
            qs = qs.filter(status=status)
        if location := form.cleaned_data.get("location"):
            qs = qs.filter(location=location)

    _ALLOWED_SORTS = {
        "name", "inventory_number", "cpu", "ram", "os",
        "status", "location__name", "updated_at",
    }
    sort      = request.GET.get("sort", "inventory_number")
    direction = request.GET.get("dir",  "asc")
    if sort not in _ALLOWED_SORTS:
        sort = "inventory_number"
    qs = qs.order_by(f"-{sort}" if direction == "desc" else sort)

    total_count = qs.count()
    paginator   = Paginator(qs, _PAGE_SIZE)
    page_num    = request.GET.get("page")
    try:
        pcs = paginator.page(page_num)
    except (PageNotAnInteger, ValueError):
        pcs = paginator.page(1)
    except EmptyPage:
        pcs = paginator.page(paginator.num_pages)

    filter_params = request.GET.copy()
    filter_params.pop("page", None)

    ctx = {
        "nav_active":   "computers",
        "pcs":          pcs,
        "form":         form,
        "sort":         sort,
        "direction":    direction,
        "total_count":  total_count,
        "filter_query": filter_params.urlencode(),
    }

    if is_htmx(request):
        return render(request, "inventory/_partials/pc_table.html", ctx)
    return render(request, "inventory/pc_list.html", ctx)


# ── HTMX modals ───────────────────────────────────────────────────────────────

def _modal_ctx(form, title: str, action_url: str, is_create: bool, pc=None) -> dict:
    """Build the context dict for the PC form modal partial."""
    return {
        "form":       form,
        "title":      title,
        "is_create":  is_create,
        "action_url": action_url,
        **({"pc": pc} if pc else {}),
    }


@login_required
def pc_create_modal(request):
    """
    HTMX modal: render and process the PC creation form.

    GET  → return the empty form inside the Bootstrap modal partial.
    POST → validate; on success return 204 + HX-Trigger to close the modal
           and refresh the table; on failure re-render with error classes.
    """
    action_url = "/pcs/modal/add/"
    if request.method == "POST":
        form = PCForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            pc.device_type = DeviceType.PC
            pc.save()
            return htmx_close_and_refresh(f"Компьютер «{pc.name}» создан.")
        return render(
            request,
            "inventory/_partials/pc_form_modal.html",
            _modal_ctx(form, "Добавить компьютер", action_url, is_create=True),
        )

    return render(
        request,
        "inventory/_partials/pc_form_modal.html",
        _modal_ctx(PCForm(), "Добавить компьютер", action_url, is_create=True),
    )


@login_required
def pc_edit_modal(request, pk: int):
    """
    HTMX modal: render and process the PC edit form.

    Returns 404 if the requested device is not of type PC.
    """
    pc         = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    action_url = f"/pcs/modal/{pk}/edit/"
    title      = f"Редактировать: {pc.name}"

    if request.method == "POST":
        form = PCForm(request.POST, instance=pc)
        if form.is_valid():
            form.save()
            return htmx_close_and_refresh(f"Компьютер «{pc.name}» обновлён.")
        return render(
            request,
            "inventory/_partials/pc_form_modal.html",
            _modal_ctx(form, title, action_url, is_create=False, pc=pc),
        )

    return render(
        request,
        "inventory/_partials/pc_form_modal.html",
        _modal_ctx(PCForm(instance=pc), title, action_url, is_create=False, pc=pc),
    )


@login_required
def pc_delete_modal(request, pk: int):
    """
    HTMX modal: confirm and execute PC deletion.

    GET  → render the confirmation modal.
    POST → delete the device and return 204 + HX-Trigger ``pcDeleted``.
    """
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        name = pc.name
        pc.delete()
        return htmx_close_and_refresh(f"Компьютер «{name}» удалён.", event="pcDeleted")
    return render(request, "inventory/_partials/pc_delete_modal.html", {"pc": pc})


# ── Full-page fallback CRUD ────────────────────────────────────────────────────

@login_required
def pc_create(request):
    """Full-page PC creation form (non-HTMX fallback)."""
    if request.method == "POST":
        form = PCForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            pc.device_type = DeviceType.PC
            pc.save()
            messages.success(request, f"Компьютер «{pc.name}» создан.")
            return redirect("pc-list")
    else:
        form = PCForm()
    return render(request, "inventory/pc_form.html", {
        "nav_active": "computers",
        "form":       form,
        "title":      "Добавить компьютер",
        "is_create":  True,
    })


@login_required
def pc_edit(request, pk: int):
    """Full-page PC edit form (non-HTMX fallback)."""
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        form = PCForm(request.POST, instance=pc)
        if form.is_valid():
            form.save()
            messages.success(request, f"Компьютер «{pc.name}» обновлён.")
            return redirect("pc-list")
    else:
        form = PCForm(instance=pc)
    return render(request, "inventory/pc_form.html", {
        "nav_active": "computers",
        "form":       form,
        "pc":         pc,
        "title":      f"Редактировать: {pc.name}",
        "is_create":  False,
    })


@login_required
def pc_delete(request, pk: int):
    """Full-page PC delete confirmation (non-HTMX fallback)."""
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        name = pc.name
        pc.delete()
        messages.success(request, f"Компьютер «{name}» удалён.")
        return redirect("pc-list")
    return render(request, "inventory/pc_confirm_delete.html", {
        "nav_active": "computers",
        "pc":         pc,
    })


# ── HTMX critical-count badge ──────────────────────────────────────────────────

@login_required
def critical_count_partial(request):
    """
    Micro-endpoint that refreshes the critical-PC badge via HTMX OOB swaps.

    Triggered from ``base.html`` on:
    * page load,
    * every 60 s (polling),
    * ``pcSaved`` / ``pcDeleted`` custom events.

    The response contains two ``hx-swap-oob="innerHTML"`` elements that
    update ``#topbar-critical-badge`` and ``#sidebar-critical-badge``
    simultaneously without re-rendering the whole page.
    """
    crit = Device.objects.filter(
        device_type=DeviceType.PC,
        status__in=[DeviceStatus.BROKEN, DeviceStatus.WRITE_OFF],
    ).count()
    return render(request, "inventory/_partials/critical_badge.html", {"crit": crit})
