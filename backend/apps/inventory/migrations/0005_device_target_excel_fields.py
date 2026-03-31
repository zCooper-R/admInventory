from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_device_organization(apps, schema_editor):
    Device = apps.get_model("inventory", "Device")
    for device in Device.objects.select_related("location__organization").all():
        if device.organization_id is None and device.location_id and device.location.organization_id:
            device.organization_id = device.location.organization_id
            device.save(update_fields=["organization"])


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0002_organization_normalized_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0004_systemsettings"),
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
        migrations.AddField(
            model_name="device",
            name="browser",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devices", to="inventory.browser", verbose_name="Браузер"),
        ),
        migrations.AddField(
            model_name="device",
            name="cpu_frequency_ghz",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name="Тактовая частота (ГГц)"),
        ),
        migrations.AddField(
            model_name="device",
            name="employee_name",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Фамилия, инициалы сотрудника"),
        ),
        migrations.AddField(
            model_name="device",
            name="has_apple_account",
            field=models.BooleanField(blank=True, null=True, verbose_name="Есть аккаунт Apple"),
        ),
        migrations.AddField(
            model_name="device",
            name="has_google_account",
            field=models.BooleanField(blank=True, null=True, verbose_name="Есть аккаунт Google"),
        ),
        migrations.AddField(
            model_name="device",
            name="has_microsoft_account",
            field=models.BooleanField(blank=True, null=True, verbose_name="Есть аккаунт Microsoft"),
        ),
        migrations.AddField(
            model_name="device",
            name="internet_speed",
            field=models.CharField(blank=True, choices=[("До 5 Мб/с", "До 5 Мб/с"), ("От 5 до 50 Мб/с", "От 5 до 50 Мб/с"), ("От 50 до 100 Мб/с", "От 50 до 100 Мб/с"), ("Свыше 100 Мб/с", "Свыше 100 Мб/с")], db_index=True, default="", max_length=32, verbose_name="Скорость интернета"),
        ),
        migrations.AddField(
            model_name="device",
            name="is_attested",
            field=models.BooleanField(blank=True, null=True, verbose_name="Аттестованный компьютер"),
        ),
        migrations.AddField(
            model_name="device",
            name="organization",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="devices", to="locations.organization", verbose_name="Организация"),
        ),
        migrations.AddField(
            model_name="device",
            name="position",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devices", to="inventory.position", verbose_name="Должность"),
        ),
        migrations.AddField(
            model_name="device",
            name="provider",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Провайдер"),
        ),
        migrations.AddField(
            model_name="device",
            name="uses_audio",
            field=models.BooleanField(blank=True, null=True, verbose_name="Работа с аудио"),
        ),
        migrations.AddField(
            model_name="device",
            name="uses_images",
            field=models.BooleanField(blank=True, null=True, verbose_name="Работа с картинками, фотографиями"),
        ),
        migrations.AddField(
            model_name="device",
            name="uses_presentations",
            field=models.BooleanField(blank=True, null=True, verbose_name="Создание презентаций"),
        ),
        migrations.AddField(
            model_name="device",
            name="uses_text",
            field=models.BooleanField(blank=True, null=True, verbose_name="Работа с текстом"),
        ),
        migrations.AddField(
            model_name="device",
            name="uses_video",
            field=models.BooleanField(blank=True, null=True, verbose_name="Работа с видео"),
        ),
        migrations.AlterField(
            model_name="device",
            name="location",
            field=models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="devices", to="locations.location", verbose_name="Площадка"),
        ),
        migrations.RunPython(backfill_device_organization, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="device",
            index=models.Index(fields=["organization", "status"], name="inventory_de_organiz_27ff6d_idx"),
        ),
        migrations.AddIndex(
            model_name="device",
            index=models.Index(fields=["position"], name="inventory_de_positio_f3f061_idx"),
        ),
        migrations.AddIndex(
            model_name="device",
            index=models.Index(fields=["browser"], name="inventory_de_browser_b8df6e_idx"),
        ),
    ]
