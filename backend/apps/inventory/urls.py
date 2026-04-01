"""
URL configuration for the Inventory web module.

All routes are included under the root prefix (see config/urls.py).

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from django.urls import path

from apps.inventory import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    # PC list (HTMX-aware — returns a partial when HX-Request header is present)
    path("pcs/", views.pc_list, name="pc-list"),
    # HTMX modal endpoints (used by HTMX only; no full-page render)
    path("pcs/modal/add/", views.pc_create_modal, name="pc-create-modal"),
    path("pcs/modal/<int:pk>/edit/", views.pc_edit_modal, name="pc-edit-modal"),
    path("pcs/modal/<int:pk>/delete/", views.pc_delete_modal, name="pc-delete-modal"),
    # Full-page CRUD fallback (usable without JavaScript)
    path("pcs/add/", views.pc_create, name="pc-create"),
    path("pcs/<int:pk>/edit/", views.pc_edit, name="pc-edit"),
    path("pcs/<int:pk>/delete/", views.pc_delete, name="pc-delete"),
    # HTMX badge partial
    path(
        "pcs/_critical-count/",
        views.critical_count_partial,
        name="critical-count-partial",
    ),
    # Import / Export / Template
    path("pcs/import/", views.pc_import, name="pc-import"),
    path("pcs/import/template/", views.pc_import_template, name="pc-import-template"),
    path("pcs/export/", views.pc_export, name="pc-export"),
    # Budget / replacement report
    path("pcs/budget/", views.budget_report, name="budget-report"),
    # System settings (admin only)
    path("settings/", views.system_settings_view, name="system-settings"),
]
