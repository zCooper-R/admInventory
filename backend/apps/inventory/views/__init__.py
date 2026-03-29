"""
Public interface for the inventory web views package.

Import any view from this package directly:

    from apps.inventory.views import dashboard, pc_list, ...

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from apps.inventory.views.views_pc import (
    critical_count_partial,
    dashboard,
    pc_create,
    pc_create_modal,
    pc_delete,
    pc_delete_modal,
    pc_edit,
    pc_edit_modal,
    pc_list,
)
from apps.inventory.views.views_budget import budget_report
from apps.inventory.views.views_import import pc_export, pc_import, pc_import_template
from apps.inventory.views.views_settings import system_settings_view

__all__ = [
    # PC
    "dashboard",
    "pc_list",
    "pc_create_modal",
    "pc_edit_modal",
    "pc_delete_modal",
    "pc_create",
    "pc_edit",
    "pc_delete",
    "critical_count_partial",
    # Budget
    "budget_report",
    # Import / Export
    "pc_import",
    "pc_export",
    "pc_import_template",
    # Settings
    "system_settings_view",
]
