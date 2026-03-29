from django.db import models


class Organization(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название организации",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


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
