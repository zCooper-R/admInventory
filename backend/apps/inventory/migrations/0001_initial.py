import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("locations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Browser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=120, unique=True, verbose_name="Браузер")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
            ],
            options={
                "verbose_name": "Браузер",
                "verbose_name_plural": "Браузеры",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Position",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=255, unique=True, verbose_name="Должность")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
            ],
            options={
                "verbose_name": "Должность",
                "verbose_name_plural": "Должности",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SystemSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "pc_min_ram_gb",
                    models.PositiveIntegerField(
                        default=8,
                        help_text="ПК с объёмом ОЗУ ниже этого значения помечается как требующий замены в бюджетном отчёте (критерий «Мало ОЗУ»).",
                        verbose_name="Мин. допустимое ОЗУ (ГБ)",
                    ),
                ),
                (
                    "pc_max_age_years",
                    models.PositiveIntegerField(
                        default=4,
                        help_text="ПК, у которых дата приобретения превышает это значение, помечаются как устаревшие.",
                        verbose_name="Макс. допустимый возраст ПК (лет)",
                    ),
                ),
                (
                    "pc_price_default",
                    models.PositiveIntegerField(
                        default=60000,
                        help_text="Начальная цена за единицу на странице «Бюджет / Замены». Пользователь может изменить её прямо на странице без сохранения.",
                        verbose_name="Стоимость замены ПК по умолчанию (₽)",
                    ),
                ),
                (
                    "system_title",
                    models.CharField(
                        default="IT Инвентарь",
                        help_text="Отображается в боковой панели и заголовке вкладки браузера.",
                        max_length=100,
                        verbose_name="Название системы",
                    ),
                ),
                (
                    "system_subtitle",
                    models.CharField(
                        blank=True,
                        default="Учёт компьютерной техники",
                        help_text="Краткое описание системы (необязательно).",
                        max_length=200,
                        verbose_name="Подзаголовок",
                    ),
                ),
            ],
            options={
                "verbose_name": "Настройки системы",
                "verbose_name_plural": "Настройки системы",
            },
        ),
        migrations.CreateModel(
            name="Device",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=255, verbose_name="Наименование")),
                (
                    "inventory_number",
                    models.CharField(db_index=True, max_length=100, unique=True, verbose_name="Инвентарный номер"),
                ),
                (
                    "device_type",
                    models.CharField(
                        choices=[("PC", "Компьютер"), ("Laptop", "Ноутбук"), ("Printer", "Принтер"), ("Other", "Прочее")],
                        db_index=True,
                        default="PC",
                        max_length=20,
                        verbose_name="Тип устройства",
                    ),
                ),
                ("cpu", models.CharField(blank=True, max_length=255, verbose_name="Процессор")),
                ("ram", models.PositiveIntegerField(blank=True, null=True, verbose_name="ОЗУ (ГБ)")),
                (
                    "storage_type",
                    models.CharField(
                        choices=[("HDD", "HDD"), ("SSD", "SSD"), ("Mixed", "HDD + SSD"), ("None", "Нет")],
                        default="HDD",
                        max_length=10,
                        verbose_name="Тип накопителя",
                    ),
                ),
                ("storage_size", models.PositiveIntegerField(blank=True, null=True, verbose_name="Объём накопителя (ГБ)")),
                ("os", models.CharField(blank=True, max_length=255, verbose_name="Операционная система")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Активен"), ("broken", "Сломан"), ("write_off", "Списан")],
                        db_index=True,
                        default="active",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                (
                    "employee_name",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="Фамилия, инициалы сотрудника"),
                ),
                (
                    "cpu_frequency_ghz",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name="Тактовая частота (ГГц)"),
                ),
                ("has_google_account", models.BooleanField(blank=True, null=True, verbose_name="Есть аккаунт Google")),
                ("has_apple_account", models.BooleanField(blank=True, null=True, verbose_name="Есть аккаунт Apple")),
                (
                    "has_microsoft_account",
                    models.BooleanField(blank=True, null=True, verbose_name="Есть аккаунт Microsoft"),
                ),
                (
                    "internet_speed",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("До 5 Мб/с", "До 5 Мб/с"),
                            ("От 5 до 50 Мб/с", "От 5 до 50 Мб/с"),
                            ("От 50 до 100 Мб/с", "От 50 до 100 Мб/с"),
                            ("Свыше 100 Мб/с", "Свыше 100 Мб/с"),
                        ],
                        db_index=True,
                        default="",
                        max_length=32,
                        verbose_name="Скорость интернета",
                    ),
                ),
                ("provider", models.CharField(blank=True, default="", max_length=255, verbose_name="Провайдер")),
                ("is_attested", models.BooleanField(blank=True, null=True, verbose_name="Аттестованный компьютер")),
                ("uses_text", models.BooleanField(blank=True, null=True, verbose_name="Работа с текстом")),
                (
                    "uses_images",
                    models.BooleanField(blank=True, null=True, verbose_name="Работа с картинками, фотографиями"),
                ),
                ("uses_presentations", models.BooleanField(blank=True, null=True, verbose_name="Создание презентаций")),
                ("uses_audio", models.BooleanField(blank=True, null=True, verbose_name="Работа с аудио")),
                ("uses_video", models.BooleanField(blank=True, null=True, verbose_name="Работа с видео")),
                (
                    "purchase_date",
                    models.DateField(
                        blank=True,
                        help_text="Реальная дата покупки. Используется для расчёта возраста.",
                        null=True,
                        verbose_name="Дата приобретения",
                    ),
                ),
                ("serial_number", models.CharField(blank=True, default="", max_length=100, verbose_name="Серийный номер")),
                (
                    "agent_hostname",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Имя компьютера в сети, заполняется автоматически агентом.",
                        max_length=255,
                        verbose_name="Hostname (агент)",
                    ),
                ),
                ("last_sync", models.DateTimeField(blank=True, null=True, verbose_name="Последняя синхронизация")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_devices",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Назначен пользователю",
                    ),
                ),
                (
                    "browser",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="devices",
                        to="inventory.browser",
                        verbose_name="Браузер",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="devices",
                        to="locations.location",
                        verbose_name="Площадка",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="devices",
                        to="locations.organization",
                        verbose_name="Организация",
                    ),
                ),
                (
                    "position",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="devices",
                        to="inventory.position",
                        verbose_name="Должность",
                    ),
                ),
            ],
            options={
                "verbose_name": "Устройство",
                "verbose_name_plural": "Устройства",
                "ordering": ["inventory_number"],
                "indexes": [
                    models.Index(fields=["status", "location"]),
                    models.Index(fields=["device_type", "status"]),
                    models.Index(fields=["inventory_number"]),
                    models.Index(fields=["organization", "status"]),
                    models.Index(fields=["position"]),
                    models.Index(fields=["browser"]),
                ],
            },
        ),
    ]
