"""Inventory app models."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.locations.models import Location, Organization


class DeviceType(models.TextChoices):
    PC = "PC", "Компьютер"
    LAPTOP = "Laptop", "Ноутбук"
    PRINTER = "Printer", "Принтер"
    OTHER = "Other", "Прочее"


class StorageType(models.TextChoices):
    HDD = "HDD", "HDD"
    SSD = "SSD", "SSD"


class DeviceStatus(models.TextChoices):
    ACTIVE = "active", "Активен"
    BROKEN = "broken", "Сломан"
    WRITE_OFF = "write_off", "Списан"


class InternetSpeed(models.TextChoices):
    UP_TO_5 = "up_to_5", "До 5 Мб/с"
    FROM_5_TO_50 = "from_5_to_50", "От 5 до 50 Мб/с"
    FROM_50_TO_100 = "from_50_to_100", "От 50 до 100 Мб/с"
    ABOVE_100 = "above_100", "Свыше 100 Мб/с"


class Browser(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Браузер")
    normalized_name = models.CharField(max_length=120, unique=True, db_index=True, verbose_name="Нормализованное имя")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Браузер"
        verbose_name_plural = "Браузеры"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.normalized_name = (self.name or "").strip().lower()
        super().save(*args, **kwargs)


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Должность")
    normalized_name = models.CharField(max_length=255, unique=True, db_index=True, verbose_name="Нормализованное имя")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Должность"
        verbose_name_plural = "Должности"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.normalized_name = " ".join((self.name or "").strip().lower().split())
        super().save(*args, **kwargs)


class Device(models.Model):
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="Наименование", db_index=True)
    inventory_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Инвентарный номер",
        db_index=True,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="Организация",
        db_index=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="Площадка",
        db_index=True,
        null=True,
        blank=True,
    )
    employee_name = models.CharField(max_length=255, blank=True, default="", verbose_name="ФИО сотрудника")
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
        verbose_name="Должность",
    )
    browser = models.ForeignKey(
        Browser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
        verbose_name="Браузер",
    )
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.PC,
        verbose_name="Тип устройства",
        db_index=True,
    )
    cpu = models.CharField(max_length=255, verbose_name="Процессор", blank=True, default="")
    cpu_frequency = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Тактовая частота (ГГц)")
    ram = models.PositiveIntegerField(verbose_name="ОЗУ (ГБ)", null=True, blank=True)
    storage_type = models.CharField(
        max_length=10,
        choices=StorageType.choices,
        default=StorageType.HDD,
        verbose_name="Тип диска",
    )
    storage_size = models.PositiveIntegerField(verbose_name="Емкость диска (ГБ)", null=True, blank=True)
    os = models.CharField(max_length=255, verbose_name="Операционная система", blank=True, default="")

    has_google_account = models.BooleanField(null=True, blank=True, verbose_name="Аккаунт Google")
    has_apple_account = models.BooleanField(null=True, blank=True, verbose_name="Аккаунт Apple")
    has_microsoft_account = models.BooleanField(null=True, blank=True, verbose_name="Аккаунт Microsoft")

    internet_speed = models.CharField(
        max_length=20,
        choices=InternetSpeed.choices,
        null=True,
        blank=True,
        verbose_name="Скорость интернета",
        db_index=True,
    )
    internet_provider = models.CharField(max_length=255, blank=True, default="", verbose_name="Провайдер")

    is_attested = models.BooleanField(null=True, blank=True, verbose_name="Аттестованный компьютер")
    work_with_text = models.BooleanField(null=True, blank=True, verbose_name="Работа с текстом")
    work_with_images = models.BooleanField(null=True, blank=True, verbose_name="Работа с картинками/фотографиями")
    create_presentations = models.BooleanField(null=True, blank=True, verbose_name="Создание презентаций")
    work_with_audio = models.BooleanField(null=True, blank=True, verbose_name="Работа с аудио")
    work_with_video = models.BooleanField(null=True, blank=True, verbose_name="Работа с видео")

    status = models.CharField(
        max_length=20,
        choices=DeviceStatus.choices,
        default=DeviceStatus.ACTIVE,
        verbose_name="Статус",
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
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата приобретения",
        help_text="Реальная дата покупки. Используется для расчета возраста.",
    )
    serial_number = models.CharField(max_length=100, blank=True, default="", verbose_name="Серийный номер")
    agent_hostname = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Hostname (агент)",
        help_text="Имя компьютера в сети, заполняется автоматически агентом.",
    )
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name="Последняя синхронизация")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"
        ordering = ["inventory_number", "id"]
        indexes = [
            models.Index(fields=["status", "organization"]),
            models.Index(fields=["device_type", "status"]),
            models.Index(fields=["inventory_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["inventory_number"],
                condition=~Q(inventory_number=""),
                name="inventory_device_inventory_number_not_blank_uniq",
            ),
        ]

    def __str__(self) -> str:
        if self.inventory_number:
            return f"{self.name or 'Устройство'} [{self.inventory_number}]"
        return self.name or f"Устройство #{self.pk}"

    def save(self, *args, **kwargs):
        if self.location_id and not self.organization_id:
            self.organization_id = self.location.organization_id
        super().save(*args, **kwargs)


class SystemSettings(models.Model):
    pc_min_ram_gb = models.PositiveIntegerField(
        default=8,
        verbose_name="Мин. допустимое ОЗУ (ГБ)",
        help_text=(
            "ПК с объемом ОЗУ ниже этого значения помечается как требующий замены "
            "в бюджетном отчете (критерий «Мало ОЗУ»)."
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
    pc_price_default = models.PositiveIntegerField(
        default=60_000,
        verbose_name="Стоимость замены ПК по умолчанию (₽)",
        help_text=(
            "Начальная цена за единицу на странице «Бюджет / Замены». "
            "Пользователь может изменить ее прямо на странице без сохранения."
        ),
    )
    system_title = models.CharField(
        max_length=100,
        default="IT Инвентарь",
        verbose_name="Название системы",
        help_text="Отображается в боковой панели и заголовке вкладки браузера.",
    )
    system_subtitle = models.CharField(
        max_length=200,
        blank=True,
        default="Учет компьютерной техники",
        verbose_name="Подзаголовок",
        help_text="Краткое описание системы (необязательно).",
    )

    class Meta:
        verbose_name = "Настройки системы"
        verbose_name_plural = "Настройки системы"

    def __str__(self) -> str:
        return "Настройки системы"

    _CACHE_KEY = "system_settings_singleton"
    _CACHE_TTL = 60

    @classmethod
    def get(cls) -> "SystemSettings":
        from django.core.cache import cache

        obj = cache.get(cls._CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls._CACHE_KEY, obj, cls._CACHE_TTL)
        return obj

    def save(self, *args, **kwargs):
        from django.core.cache import cache

        super().save(*args, **kwargs)
        cache.delete(self._CACHE_KEY)
