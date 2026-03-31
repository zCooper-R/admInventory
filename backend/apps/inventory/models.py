"""
Inventory app models.

Defines the core Device model and supporting enumerations, plus the
singleton SystemSettings model that stores operator-configurable
parameters (thresholds, pricing, branding) without requiring a
server restart or code redeploy.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from django.db import models
from django.conf import settings

from apps.locations.models import Location


class DeviceType(models.TextChoices):
    PC = "PC", "Компьютер"
    LAPTOP = "Laptop", "Ноутбук"
    PRINTER = "Printer", "Принтер"
    OTHER = "Other", "Прочее"


class StorageType(models.TextChoices):
    HDD = "HDD", "HDD"
    SSD = "SSD", "SSD"
    MIXED = "Mixed", "HDD + SSD"
    NONE = "None", "Нет"


class DeviceStatus(models.TextChoices):
    ACTIVE = "active", "Активен"
    BROKEN = "broken", "Сломан"
    WRITE_OFF = "write_off", "Списан"


class Device(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Наименование",
        db_index=True,
    )
    inventory_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Инвентарный номер",
        db_index=True,
    )
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.PC,
        verbose_name="Тип устройства",
        db_index=True,
    )
    cpu = models.CharField(
        max_length=255,
        verbose_name="Процессор",
        blank=True,
    )
    ram = models.PositiveIntegerField(
        verbose_name="ОЗУ (ГБ)",
        null=True,
        blank=True,
    )
    storage_type = models.CharField(
        max_length=10,
        choices=StorageType.choices,
        default=StorageType.HDD,
        verbose_name="Тип накопителя",
    )
    storage_size = models.PositiveIntegerField(
        verbose_name="Объём накопителя (ГБ)",
        null=True,
        blank=True,
    )
    os = models.CharField(
        max_length=255,
        verbose_name="Операционная система",
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=DeviceStatus.choices,
        default=DeviceStatus.ACTIVE,
        verbose_name="Статус",
        db_index=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="Площадка",
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_devices",
        verbose_name="Назначен пользователю",
    )
    # ── Identification / provenance ─────────────────────────────────────────────
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата приобретения",
        help_text="Реальная дата покупки. Используется для расчёта возраста.",
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Серийный номер",
    )

    # ── Agent sync metadata ──────────────────────────────────────────────────────
    agent_hostname = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Hostname (агент)",
        help_text="Имя компьютера в сети, заполняется автоматически агентом.",
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последняя синхронизация",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"
        ordering = ["inventory_number"]
        indexes = [
            models.Index(fields=["status", "location"]),
            models.Index(fields=["device_type", "status"]),
            models.Index(fields=["inventory_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.inventory_number}]"


# ── Singleton settings ─────────────────────────────────────────────────────────

class SystemSettings(models.Model):
    """
    Singleton model for operator-configurable system parameters.

    Only one row (pk=1) should ever exist.  Use ``SystemSettings.get()``
    rather than querying directly.  All changes take effect immediately
    (no redeploy required).
    """

    # ── Replacement-analysis thresholds ──────────────────────────────────────
    pc_min_ram_gb = models.PositiveIntegerField(
        default=8,
        verbose_name="Мин. допустимое ОЗУ (ГБ)",
        help_text=(
            "ПК с объёмом ОЗУ ниже этого значения помечается как требующий замены "
            "в бюджетном отчёте (критерий «Мало ОЗУ»)."
        ),
    )
    pc_max_age_years = models.PositiveIntegerField(
        default=4,
        verbose_name="Макс. допустимый возраст ПК (лет)",
        help_text=(
            "ПК, у которых дата приобретения превышает это значение, "
            "помечаются как устаревшие."
        ),
    )

    # ── Budget defaults ───────────────────────────────────────────────────────
    pc_price_default = models.PositiveIntegerField(
        default=60_000,
        verbose_name="Стоимость замены ПК по умолчанию (₽)",
        help_text=(
            "Начальная цена за единицу на странице «Бюджет / Замены». "
            "Пользователь может изменить её прямо на странице без сохранения."
        ),
    )

    # ── Branding ─────────────────────────────────────────────────────────────
    system_title = models.CharField(
        max_length=100,
        default="IT Инвентарь",
        verbose_name="Название системы",
        help_text="Отображается в боковой панели и заголовке вкладки браузера.",
    )
    system_subtitle = models.CharField(
        max_length=200,
        blank=True,
        default="Учёт компьютерной техники",
        verbose_name="Подзаголовок",
        help_text="Краткое описание системы (необязательно).",
    )

    class Meta:
        verbose_name = "Настройки системы"

    def __str__(self) -> str:
        return "Настройки системы"

    _CACHE_KEY = "system_settings_singleton"
    _CACHE_TTL = 60  # seconds

    @classmethod
    def get(cls) -> "SystemSettings":
        """
        Return the singleton settings row, creating it with defaults if absent.

        Results are cached in Django's default cache backend for
        ``_CACHE_TTL`` seconds so successive requests within the same
        minute share one DB hit.  The cache is invalidated automatically
        whenever the record is saved (see :meth:`save`).
        """
        from django.core.cache import cache

        obj = cache.get(cls._CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls._CACHE_KEY, obj, cls._CACHE_TTL)
        return obj

    def save(self, *args, **kwargs):
        """Save and immediately invalidate the cached singleton."""
        from django.core.cache import cache

        super().save(*args, **kwargs)
        cache.delete(self._CACHE_KEY)
