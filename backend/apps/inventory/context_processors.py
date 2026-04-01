"""
Template context processors for the Inventory app.

Injects site-wide variables into every Django template context so they
don't have to be passed explicitly from each view.

Injected variables
------------------
site_settings  — :class:`~apps.inventory.models.SystemSettings` singleton
APP_VERSION    — current application version string (e.g. "0.1.0")

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from __future__ import annotations

import logging

from config.version import VERSION

logger = logging.getLogger(__name__)


def site_settings(request):
    """
    Inject ``site_settings`` and ``APP_VERSION`` into every template.

    ``site_settings`` falls back gracefully to an unsaved
    :class:`~apps.inventory.models.SystemSettings` instance with default
    values when the database is unavailable (e.g. during migrations).

    Usage in templates::

        {{ site_settings.system_title }}
        {{ site_settings.pc_price_default }}
        {{ APP_VERSION }}
    """
    ctx = {"APP_VERSION": VERSION}
    try:
        from apps.inventory.models import SystemSettings

        ctx["site_settings"] = SystemSettings.get()
    except Exception as exc:
        logger.debug("site_settings context processor fallback: %s", exc)
        try:
            from apps.inventory.models import SystemSettings

            ctx["site_settings"] = SystemSettings()
        except Exception:
            ctx["site_settings"] = None
    return ctx
