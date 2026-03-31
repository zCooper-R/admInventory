from django.db import models
from django.db.models.functions import Lower

from .normalization import normalize_organization_name


class Organization(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название организации",
    )
    normalized_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Нормализованное название",
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


class Location(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название площадки",
    )
    address = models.TextField(
        verbose_name="Адрес",
        blank=True,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="locations",
        verbose_name="Организация",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Площадка"
        verbose_name_plural = "Площадки"
        ordering = ["organization", "name"]
        unique_together = ("name", "organization")

    def __str__(self) -> str:
        return f"{self.organization.name} — {self.name}"
