from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Администратор"
    MANAGER = "manager", "Менеджер"
    USER = "user", "Пользователь"


class User(AbstractUser):
    full_name = models.CharField(
        max_length=255,
        verbose_name="Полное имя",
        blank=True,
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name="Роль",
        db_index=True,
    )
    location = models.ForeignKey(
        "locations.Location",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="responsible_users",
        verbose_name="Площадка (для менеджеров)",
        help_text="Если задана — менеджер видит только ПК этой площадки.",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.full_name or self.username

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == UserRole.MANAGER
