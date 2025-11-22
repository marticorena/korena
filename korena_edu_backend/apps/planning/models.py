from django.conf import settings
from django.db import models
from django.utils import timezone


class PlanningLevel(models.TextChoices):
    TEACHER = "TEACHER", "Nivel Docente"
    CLASSROOM = "CLASSROOM", "Nivel Aula"


class PlanningSheet(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="planning_sheets",
    )
    level = models.CharField(
        max_length=20,
        choices=PlanningLevel.choices,
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    sheet_type = models.CharField(max_length=50)

    grade = models.CharField(max_length=50, blank=True)
    area = models.CharField(max_length=100, blank=True)
    school_year = models.PositiveIntegerField(default=2025)

    columns_schema = models.JSONField(
        default=list,
        help_text="Column definition used by the frontend grid component.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class PlanningRow(models.Model):
    sheet = models.ForeignKey(
        PlanningSheet,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    index = models.PositiveIntegerField()
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["index"]

    def __str__(self) -> str:
        return f"{self.sheet.title} - row {self.index}"
