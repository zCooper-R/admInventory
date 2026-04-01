from __future__ import annotations

import json
import logging
from datetime import timedelta

from apps.inventory.forms import PCFilterForm, PCForm
from apps.inventory.models import Device, DeviceType, ReplacementStatus
from apps.inventory.services.budget import build_budget_report, get_cached_budget_report
from apps.inventory.views.common import htmx_close_and_refresh, is_htmx, pc_qs
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, Count, F, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce, Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

_PAGE_SIZE = 25
logger = logging.getLogger(__name__)


def _apply_sorting(qs, sort: str, direction: str):
    sort_map = {
        "inventory_number": Lower(Coalesce("inventory_number", Value(""))),
        "organization__name": Lower(Coalesce("organization__name", Value(""))),
        "os": Lower(Coalesce("os", Value(""))),
        "cpu_model": Lower(Coalesce("cpu_model", Value(""))),
        "cpu_frequency": Coalesce("cpu_frequency", Value(-1.0)),
        "ram": Coalesce("ram", Value(-1)),
        "storage_type": Lower(Coalesce("storage_type", Value(""))),
        "storage_size": Coalesce("storage_size", Value(-1)),
        "browser__name": Lower(Coalesce("browser__name", Value(""))),
        "employee_name": Lower(Coalesce("employee_name", Value(""))),
        "position__name": Lower(Coalesce("position__name", Value(""))),
        "provider": Lower(Coalesce("provider", Value(""))),
        "internet_speed": Lower(Coalesce("internet_speed", Value(""))),
        "is_certified": Coalesce("is_certified", Value(False)),
        "replacement_status": Lower(Coalesce("replacement_status", Value(""))),
        "replacement_score": Coalesce("replacement_score", Value(-1)),
        "updated_at": F("updated_at"),
    }
    expr = sort_map.get(sort, sort_map["inventory_number"])
    order_expr = (
        expr.desc(nulls_last=True) if direction == "desc" else expr.asc(nulls_last=True)
    )
    return qs.order_by(order_expr, "id")


def _apply_dashboard_filters(qs, request):
    organization_id = request.GET.get("organization", "").strip()
    replacement_status = request.GET.get("replacement_status", "").strip()
    storage_type = request.GET.get("storage_type", "").strip()

    if organization_id:
        qs = qs.filter(organization_id=organization_id)
    if replacement_status in {
        ReplacementStatus.OK,
        ReplacementStatus.ATTENTION,
        ReplacementStatus.REPLACE,
    }:
        qs = qs.filter(replacement_status=replacement_status)
    if storage_type in {"SSD", "HDD"}:
        qs = qs.filter(storage_type=storage_type)

    return qs


@login_required
def dashboard(request):
    base_qs = pc_qs(request.user)
    qs = _apply_dashboard_filters(base_qs, request)

    price_raw = request.GET.get("price_per_pc", "").strip()
    settings_price = get_cached_budget_report().price_per_pc
    try:
        price_per_pc = int(price_raw) if price_raw else int(settings_price)
    except ValueError:
        price_per_pc = int(settings_price)
    price_per_pc = max(1000, min(price_per_pc, 5_000_000))
    # Global budget must be fresh, not from cache.
    budget_report = build_budget_report()

    total = qs.count()
    replace_count = qs.filter(replacement_status=ReplacementStatus.REPLACE).count()
    attention_count = qs.filter(replacement_status=ReplacementStatus.ATTENTION).count()
    ok_count = qs.filter(replacement_status=ReplacementStatus.OK).count()
    critical_pct = round((replace_count / total) * 100, 1) if total else 0

    now = timezone.now()
    updated_7 = qs.filter(updated_at__gte=now - timedelta(days=7)).count()
    updated_30 = qs.filter(updated_at__gte=now - timedelta(days=30)).count()
    created_7 = qs.filter(created_at__gte=now - timedelta(days=7)).count()
    created_30 = qs.filter(created_at__gte=now - timedelta(days=30)).count()

    top_risk_organizations = list(
        qs.values("organization__name")
        .annotate(
            total_devices=Count("id"),
            replace_count=Sum(
                Case(
                    When(replacement_status=ReplacementStatus.REPLACE, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            attention_count=Sum(
                Case(
                    When(replacement_status=ReplacementStatus.ATTENTION, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )
        .annotate(risk_score=F("replace_count") * 2 + F("attention_count"))
        .order_by("-risk_score", "-replace_count", "organization__name")[:8]
    )

    replacement_chart = {
        "labels": ["Норма", "Внимание", "Замена"],
        "data": [ok_count, attention_count, replace_count],
        "colors": ["#16a34a", "#d97706", "#dc2626"],
    }
    org_chart = {
        "labels": [i["organization__name"] for i in top_risk_organizations],
        "data": [i["risk_score"] for i in top_risk_organizations],
    }

    export_params = request.GET.copy()
    export_params.pop("page", None)
    export_url = "/pcs/export/"
    if export_params.urlencode():
        export_url += f"?{export_params.urlencode()}"

    return render(
        request,
        "inventory/dashboard.html",
        {
            "nav_active": "dashboard",
            "organizations": base_qs.values("organization_id", "organization__name")
            .distinct()
            .order_by("organization__name"),
            "selected_organization": request.GET.get("organization", ""),
            "selected_replacement_status": request.GET.get("replacement_status", ""),
            "selected_storage_type": request.GET.get("storage_type", ""),
            "price_per_pc": price_per_pc,
            "export_url": export_url,
            "total": total,
            "replace_count": replace_count,
            "attention_count": attention_count,
            "ok_count": ok_count,
            "critical_pct": critical_pct,
            "updated_7": updated_7,
            "updated_30": updated_30,
            "created_7": created_7,
            "created_30": created_30,
            "top_risk_organizations": top_risk_organizations,
            "dashboard_budget_cost": replace_count * price_per_pc,
            "status_chart_json": json.dumps(replacement_chart),
            "location_chart_json": json.dumps(org_chart),
            "recent_pcs": qs.order_by("-updated_at")[:8],
            "critical_devices": qs.filter(
                replacement_status__in=[
                    ReplacementStatus.REPLACE,
                    ReplacementStatus.ATTENTION,
                ]
            )
            .annotate(
                status_order=Case(
                    When(replacement_status=ReplacementStatus.REPLACE, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_order", "replacement_score", "-updated_at")[:10],
            "budget_report": budget_report,
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
        "os",
        "cpu_model",
        "cpu_frequency",
        "ram",
        "storage_type",
        "storage_size",
        "browser__name",
        "employee_name",
        "position__name",
        "provider",
        "internet_speed",
        "is_certified",
        "replacement_status",
        "replacement_score",
        "updated_at",
    }
    sort = request.GET.get("sort", "inventory_number")
    direction = request.GET.get("dir", "asc")
    if sort not in allowed_sorts:
        sort = "inventory_number"
    if direction not in {"asc", "desc"}:
        direction = "asc"
    qs = _apply_sorting(qs, sort, direction)

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
    return {
        "form": form,
        "title": title,
        "is_create": is_create,
        "action_url": action_url,
        **({"pc": pc} if pc else {}),
    }


@login_required
def pc_create_modal(request):
    action_url = "/pcs/modal/add/"
    if request.method == "POST":
        form = PCForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            pc.device_type = DeviceType.PC
            pc.save()
            logger.info(
                "Создано устройство через модалку: user=%s inventory=%s",
                request.user.username,
                pc.inventory_number,
            )
            return htmx_close_and_refresh(
                f"Устройство [{pc.inventory_number}] создано."
            )
        return render(
            request,
            "inventory/_partials/pc_form_modal.html",
            _modal_ctx(form, "Добавить устройство", action_url, True),
        )
    return render(
        request,
        "inventory/_partials/pc_form_modal.html",
        _modal_ctx(PCForm(), "Добавить устройство", action_url, True),
    )


@login_required
def pc_edit_modal(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    action_url = f"/pcs/modal/{pk}/edit/"
    title = f"Редактировать: {pc.inventory_number}"

    if request.method == "POST":
        form = PCForm(request.POST, instance=pc)
        if form.is_valid():
            form.save()
            logger.info(
                "Обновлено устройство через модалку: user=%s inventory=%s",
                request.user.username,
                pc.inventory_number,
            )
            return htmx_close_and_refresh(
                f"Устройство [{pc.inventory_number}] обновлено."
            )
        return render(
            request,
            "inventory/_partials/pc_form_modal.html",
            _modal_ctx(form, title, action_url, False, pc),
        )

    return render(
        request,
        "inventory/_partials/pc_form_modal.html",
        _modal_ctx(PCForm(instance=pc), title, action_url, False, pc),
    )


@login_required
def pc_delete_modal(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        inv = pc.inventory_number
        pc.delete()
        logger.info(
            "Удалено устройство через модалку: user=%s inventory=%s",
            request.user.username,
            inv,
        )
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
            logger.info(
                "Создано устройство: user=%s inventory=%s",
                request.user.username,
                pc.inventory_number,
            )
            messages.success(request, f"Устройство [{pc.inventory_number}] создано.")
            return redirect("pc-list")
    else:
        form = PCForm()
    return render(
        request,
        "inventory/pc_form.html",
        {
            "nav_active": "computers",
            "form": form,
            "title": "Добавить устройство",
            "is_create": True,
        },
    )


@login_required
def pc_edit(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        form = PCForm(request.POST, instance=pc)
        if form.is_valid():
            form.save()
            logger.info(
                "Обновлено устройство: user=%s inventory=%s",
                request.user.username,
                pc.inventory_number,
            )
            messages.success(request, f"Устройство [{pc.inventory_number}] обновлено.")
            return redirect("pc-list")
    else:
        form = PCForm(instance=pc)
    return render(
        request,
        "inventory/pc_form.html",
        {
            "nav_active": "computers",
            "form": form,
            "pc": pc,
            "title": f"Редактировать: {pc.inventory_number}",
            "is_create": False,
        },
    )


@login_required
def pc_delete(request, pk: int):
    pc = get_object_or_404(Device, pk=pk, device_type=DeviceType.PC)
    if request.method == "POST":
        inv = pc.inventory_number
        pc.delete()
        logger.info(
            "Удалено устройство: user=%s inventory=%s", request.user.username, inv
        )
        messages.success(request, f"Устройство [{inv}] удалено.")
        return redirect("pc-list")
    return render(
        request,
        "inventory/pc_confirm_delete.html",
        {"nav_active": "computers", "pc": pc},
    )


def critical_count_partial(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=204)
    crit = Device.objects.filter(
        device_type=DeviceType.PC, replacement_status=ReplacementStatus.REPLACE
    ).count()
    return render(request, "inventory/_partials/critical_badge.html", {"crit": crit})
