"""
System settings view.

Accessible only to superusers and users with ``role=admin``.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.inventory.forms import SystemSettingsForm
from apps.inventory.models import SystemSettings


@login_required
def system_settings_view(request):
    """
    Singleton system-settings page.

    Displays and saves the :class:`~apps.inventory.models.SystemSettings` record.
    Also exposes the ``AGENT_API_KEY`` (read-only) so operators can copy it
    into the agent scripts without opening a server console.

    Access is restricted to superusers and users with ``role=admin``.
    All other authenticated users are redirected to the dashboard.
    """
    if not (request.user.is_superuser or getattr(request.user, "role", "") == "admin"):
        messages.error(request, "Доступ к настройкам разрешён только администраторам.")
        return redirect("dashboard")

    instance = SystemSettings.get()

    if request.method == "POST":
        form = SystemSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Настройки успешно сохранены.")
            return redirect("system-settings")
    else:
        form = SystemSettingsForm(instance=instance)

    agent_key = getattr(django_settings, "AGENT_API_KEY", "не задан")

    return render(request, "inventory/settings.html", {
        "nav_active": "settings",
        "form":       form,
        "agent_key":  agent_key,
    })
