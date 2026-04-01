"""
Django signals for the Inventory application.

Currently registered signals
-----------------------------
Device post_save / post_delete
    Invalidates the cached budget report so the next request sees
    up-to-date replacement data after any PC change.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from apps.inventory.models import Device
from apps.inventory.services.budget import invalidate_budget_cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver([post_save, post_delete], sender=Device)
def device_changed(sender, **kwargs) -> None:
    """Evict the budget report cache whenever a Device record changes."""
    invalidate_budget_cache()
