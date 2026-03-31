import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ImportLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="imports/", verbose_name="Файл Excel")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ожидает"),
                            ("processing", "Обрабатывается"),
                            ("success", "Успешно"),
                            ("partial", "Частично"),
                            ("failed", "Ошибка"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("total_rows", models.PositiveIntegerField(default=0, verbose_name="Всего строк")),
                ("created_count", models.PositiveIntegerField(default=0, verbose_name="Создано")),
                ("updated_count", models.PositiveIntegerField(default=0, verbose_name="Обновлено")),
                ("error_count", models.PositiveIntegerField(default=0, verbose_name="Ошибок")),
                ("errors", models.JSONField(default=list, verbose_name="Детали ошибок")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="import_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Загрузил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Лог импорта",
                "verbose_name_plural": "Логи импорта",
                "ordering": ["-created_at"],
            },
        ),
    ]
