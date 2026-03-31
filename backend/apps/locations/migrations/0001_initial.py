import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True, verbose_name="Название организации")),
                (
                    "normalized_name",
                    models.CharField(
                        db_index=True,
                        editable=False,
                        max_length=255,
                        unique=True,
                        verbose_name="Нормализованное название",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
            ],
            options={
                "verbose_name": "Организация",
                "verbose_name_plural": "Организации",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название площадки")),
                ("address", models.TextField(blank=True, verbose_name="Адрес")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                (
                    "organization",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="locations",
                        to="locations.organization",
                        verbose_name="Организация",
                    ),
                ),
            ],
            options={
                "verbose_name": "Площадка",
                "verbose_name_plural": "Площадки",
                "ordering": ["organization", "name"],
                "unique_together": {("name", "organization")},
            },
        ),
    ]
