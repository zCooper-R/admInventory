from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventory"
    verbose_name = "Инвентарь"

    def ready(self) -> None:
        """Import signals so they are registered when Django starts."""
        import apps.inventory.signals  # noqa: F401
