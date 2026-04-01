from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_device_target_model_cleanup"),
    ]

    operations = [
        migrations.AlterField(
            model_name="device",
            name="replacement_status",
            field=models.CharField(
                choices=[
                    ("ok", "Норма"),
                    ("attention", "Требует внимания"),
                    ("replace", "Требует замены"),
                ],
                db_index=True,
                default="attention",
                max_length=20,
                verbose_name="Статус замены",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_attention_threshold",
            field=models.PositiveIntegerField(
                default=3, verbose_name="Порог статуса 'внимание'"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_cpu_excellent_score",
            field=models.PositiveIntegerField(
                default=3, verbose_name="Баллы процессора: отличный"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_cpu_good_score",
            field=models.PositiveIntegerField(
                default=2, verbose_name="Баллы процессора: хороший"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_cpu_medium_score",
            field=models.PositiveIntegerField(
                default=1, verbose_name="Баллы процессора: средний"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_cpu_unknown_score",
            field=models.PositiveIntegerField(
                default=1, verbose_name="Баллы процессора: нераспознанный"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_cpu_weak_score",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Баллы процессора: слабый"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ok_threshold",
            field=models.PositiveIntegerField(
                default=6, verbose_name="Порог статуса 'норма'"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_high_score",
            field=models.PositiveIntegerField(
                default=2, verbose_name="Баллы ОЗУ: хороший уровень"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_high_threshold_gb",
            field=models.PositiveIntegerField(
                default=32, verbose_name="Порог ОЗУ: высокий (ГБ)"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_low_score",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Баллы ОЗУ: низкий уровень"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_low_threshold_gb",
            field=models.PositiveIntegerField(
                default=8, verbose_name="Порог ОЗУ: низкий (ГБ)"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_mid_score",
            field=models.PositiveIntegerField(
                default=1, verbose_name="Баллы ОЗУ: средний уровень"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_mid_threshold_gb",
            field=models.PositiveIntegerField(
                default=16, verbose_name="Порог ОЗУ: средний (ГБ)"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_ram_top_score",
            field=models.PositiveIntegerField(
                default=3, verbose_name="Баллы ОЗУ: высокий уровень"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_storage_hdd_score",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Баллы диска HDD"
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="replacement_storage_ssd_score",
            field=models.PositiveIntegerField(
                default=2, verbose_name="Баллы диска SSD"
            ),
        ),
    ]
