"""
Migration: add SystemSettings singleton model.

This table stores operator-configurable parameters (thresholds, pricing,
branding) that can be edited from the web UI without a server restart.
Only one row (pk=1) is ever used; it is created on first access via
SystemSettings.get().
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_device_agent_hostname_device_last_sync_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
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
            },
        ),
    ]
