"""
System settings view.

Accessible only to superusers and users with ``role=admin``.
"""

from __future__ import annotations

import logging

from apps.inventory.forms import SystemSettingsForm
from apps.inventory.models import SystemSettings
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

web_logger = logging.getLogger("apps.inventory.views")
audit_logger = logging.getLogger("apps.inventory.audit")


@login_required
def system_settings_view(request):
    """Singleton system settings page."""
    if not (request.user.is_superuser or getattr(request.user, "role", "") == "admin"):
        messages.error(request, "Доступ к настройкам разрешён только администраторам.")
        return redirect("dashboard")

    instance = SystemSettings.get()

    if request.method == "POST":
        form = SystemSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            changed_fields = {
                field: {
                    "old": form.initial.get(field),
                    "new": form.cleaned_data.get(field),
                }
                for field in form.changed_data
            }
            form.save()
            if changed_fields:
                web_logger.info(
                    "Сохранены системные настройки: user=%s changed=%s",
                    request.user.username,
                    ",".join(form.changed_data),
                )
                audit_logger.info(
                    "Изменены параметры replacement/system: %s",
                    changed_fields,
                    extra={
                        "user": request.user.username,
                        "action": "system_settings_update",
                    },
                )
            messages.success(request, "Настройки успешно сохранены.")
            return redirect("system-settings")
        web_logger.warning(
            "Ошибка валидации системных настроек: user=%s", request.user.username
        )
    else:
        form = SystemSettingsForm(instance=instance)

    agent_key = getattr(django_settings, "AGENT_API_KEY", "не задан")

    return render(
        request,
        "inventory/settings.html",
        {
            "nav_active": "settings",
            "form": form,
            "agent_key": agent_key,
        },
    )
