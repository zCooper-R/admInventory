from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.inventory.forms import PCFilterForm, PCForm
from apps.inventory.models import Device, DeviceType, ReplacementStatus
from apps.inventory.services.budget import get_cached_budget_report
from apps.inventory.views.common import htmx_close_and_refresh, is_htmx, pc_qs

_PAGE_SIZE = 25


@login_required
def dashboard(request):
    qs = pc_qs(request.user)
    total = qs.count()
    replace_count = qs.filter(replacement_status=ReplacementStatus.REPLACE).count()
    attention_count = qs.filter(replacement_status=ReplacementStatus.ATTENTION).count()
    ok_count = qs.filter(replacement_status=ReplacementStatus.OK).count()

    replacement_chart = {
        "labels": ["OK", "Внимание", "Замена"],
        "data": [ok_count, attention_count, replace_count],
        "colors": ["#16a34a", "#d97706", "#dc2626"],
    }
    org_qs = qs.values("organization__name").annotate(count=Count("id")).order_by("-count")[:12]
    org_chart = {
        "labels": [i["organization__name"] for i in org_qs],
        "data": [i["count"] for i in org_qs],
    }

    return render(
        request,
        "inventory/dashboard.html",
        {
            "nav_active": "dashboard",
            "total": total,
            "replace_count": replace_count,
            "attention_count": attention_count,
            "ok_count": ok_count,
            "status_chart_json": json.dumps(replacement_chart),
            "location_chart_json": json.dumps(org_chart),
            "recent_pcs": qs.order_by("-updated_at")[:8],
            "budget_report": get_cached_budget_report(),
        },
    )


@login_required
def pc_list(request):
    qs = pc_qs(request.user)
    form = PCFilterForm(request.GET)

    if form.is_valid():
        if s := form.cleaned_data.get("search"):
            qs = qs.filter(
                Q(inventory_number__icontains=s)
                | Q(employee_name__icontains=s)
                | Q(organization__name__icontains=s)
                | Q(cpu_model__icontains=s)
                | Q(os__icontains=s)
            )
        if organization := form.cleaned_data.get("organization"):
            qs = qs.filter(organization=organization)
        if position := form.cleaned_data.get("position"):
            qs = qs.filter(position=position)
        if browser := form.cleaned_data.get("browser"):
            qs = qs.filter(browser=browser)
        if replacement_status := form.cleaned_data.get("replacement_status"):
            qs = qs.filter(replacement_status=replacement_status)
        if storage_type := form.cleaned_data.get("storage_type"):
            qs = qs.filter(storage_type=storage_type)
        if internet_speed := form.cleaned_data.get("internet_speed"):
            qs = qs.filter(internet_speed=internet_speed)

    allowed_sorts = {
        "inventory_number",
        "organization__name",
        "employee_name",
        "ram",
        "storage_type",
        "replacement_status",
        "replacement_score",
        "updated_at",
    }
    sort = request.GET.get("sort", "inventory_number")
    direction = request.GET.get("dir", "asc")
    if sort not in allowed_sorts:
        sort = "inventory_number"
    qs = qs.order_by(f"-{sort}" if direction == "desc" else sort)

    paginator = Paginator(qs, _PAGE_SIZE)
    page_num = request.GET.get("page")
    try:
        devices = paginator.page(page_num)
    except (PageNotAnInteger, ValueError):
        devices = paginator.page(1)
    except EmptyPage:
        devices = paginator.page(paginator.num_pages)

    filter_params = request.GET.copy()
    filter_params.pop("page", None)

    ctx = {
        "nav_active": "computers",
        "pcs": devices,
        "form": form,
        "sort": sort,
        "direction": direction,
        "total_count": qs.count(),
        "filter_query": filter_params.urlencode(),
    }

    if is_htmx(request):
        return render(request, "inventory/_partials/pc_table.html", ctx)
    return render(request, "inventory/pc_list.html", ctx)


def _modal_ctx(form, title: str, action_url: str, is_create: bool, pc=None) -> dict:
    return {"form": form, "title": title, "is_create": is_create, "action_url": action_url, **({"pc": pc} if pc else {})}


@login_required
def pc_create_modal(request):
    action_url = "/pcs/modal/add/"
    if request.method == "POST":
        form = PCForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            pc.device_type = DeviceType.PC
            pc.save()
            return htmx_close_and_refresh(f"Устройство [{pc.inventory_number}] создано.")
        return render(request, "inventory/_partials/pc_form_modal.html", _modal_ctx(form, "Добавить устройство", action_url, True))
    return render(request, "inventory/_partials/pc_form_modal.html", _modal_ctx(PCForm(), "Добавить устройство", action_url, True))


@login_required
def pc_edit_modal(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    action_url = f"/pcs/modal/{pk}/edit/"
    title = f"Редактировать: {pc.inventory_number}"

    if request.method == "POST":
        form = PCForm(request.POST, instance=pc)
        if form.is_valid():
            form.save()
            return htmx_close_and_refresh(f"Устройство [{pc.inventory_number}] обновлено.")
        return render(request, "inventory/_partials/pc_form_modal.html", _modal_ctx(form, title, action_url, False, pc))

    return render(request, "inventory/_partials/pc_form_modal.html", _modal_ctx(PCForm(instance=pc), title, action_url, False, pc))


@login_required
def pc_delete_modal(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        inv = pc.inventory_number
        pc.delete()
        return htmx_close_and_refresh(f"Устройство [{inv}] удалено.", event="pcDeleted")
    return render(request, "inventory/_partials/pc_delete_modal.html", {"pc": pc})


@login_required
def pc_create(request):
    if request.method == "POST":
        form = PCForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            pc.device_type = DeviceType.PC
            pc.save()
            messages.success(request, f"Устройство [{pc.inventory_number}] создано.")
            return redirect("pc-list")
    else:
        form = PCForm()
    return render(request, "inventory/pc_form.html", {"nav_active": "computers", "form": form, "title": "Добавить устройство", "is_create": True})


@login_required
def pc_edit(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        form = PCForm(request.POST, instance=pc)
        if form.is_valid():
            form.save()
            messages.success(request, f"Устройство [{pc.inventory_number}] обновлено.")
            return redirect("pc-list")
    else:
        form = PCForm(instance=pc)
    return render(request, "inventory/pc_form.html", {"nav_active": "computers", "form": form, "pc": pc, "title": f"Редактировать: {pc.inventory_number}", "is_create": False})


@login_required
def pc_delete(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        inv = pc.inventory_number
        pc.delete()
        messages.success(request, f"Устройство [{inv}] удалено.")
        return redirect("pc-list")
    return render(request, "inventory/pc_confirm_delete.html", {"nav_active": "computers", "pc": pc})


@login_required
def critical_count_partial(request):
    crit = Device.objects.filter(device_type=DeviceType.PC, replacement_status=ReplacementStatus.REPLACE).count()
    return render(request, "inventory/_partials/critical_badge.html", {"crit": crit})
