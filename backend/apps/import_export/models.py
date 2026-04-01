from django.conf import settings
from django.db import models


class ImportStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    PROCESSING = "processing", "Обрабатывается"
    SUCCESS = "success", "Успешно"
    PARTIAL = "partial", "Частично"
    FAILED = "failed", "Ошибка"


class ImportLog(models.Model):
    file = models.FileField(
        upload_to="imports/",
        verbose_name="Файл Excel",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="import_logs",
        verbose_name="Загрузил",
    )
    status = models.CharField(
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
        verbose_name="Статус",
    )
    total_rows = models.PositiveIntegerField(default=0, verbose_name="Всего строк")
    created_count = models.PositiveIntegerField(default=0, verbose_name="Создано")
    updated_count = models.PositiveIntegerField(default=0, verbose_name="Обновлено")
    error_count = models.PositiveIntegerField(default=0, verbose_name="Ошибок")
    errors = models.JSONField(default=list, verbose_name="Детали ошибок")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Лог импорта"
        verbose_name_plural = "Логи импорта"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Импорт #{self.pk} — {self.get_status_display()} ({self.created_at:%d.%m.%Y %H:%M})"
