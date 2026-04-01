"""
Root URL configuration.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from apps.inventory.models import SystemSettings
from config.version import APP_NAME, RELEASE_DATE, VERSION
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def apply_admin_branding() -> None:
    admin.site.site_title = "IT Инвентарь Admin"
    try:
        cfg = SystemSettings.get()
        admin.site.site_header = cfg.system_title or "IT Инвентарь"
        admin.site.index_title = cfg.system_subtitle or "Управление системой"
    except Exception:
        # During early startup/migrations DB can be unavailable.
        admin.site.site_header = "IT Инвентарь"
        admin.site.index_title = "Управление системой"


apply_admin_branding()


def api_version(request):
    """GET /api/version/ — returns current application version as JSON."""
    return JsonResponse(
        {
            "app": APP_NAME,
            "version": VERSION,
            "released": RELEASE_DATE,
            "status": "ok",
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.inventory.urls")),
    path("api/v1/", include("config.api_router")),
    path("api/version/", api_version, name="api-version"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
