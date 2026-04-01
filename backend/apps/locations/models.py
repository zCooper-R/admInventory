from django.db import models
from django.db.models.functions import Lower

from .normalization import normalize_organization_name


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название организации")
    normalized_name = models.CharField(
        max_length=255, unique=True, verbose_name="Нормализованное название"
    )
    address = models.CharField(
        max_length=500, blank=True, default="", verbose_name="Адрес"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("normalized_name"),
                name="locations_org_normalized_name_ci_uniq",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_organization_name(self.name)
        super().save(*args, **kwargs)
