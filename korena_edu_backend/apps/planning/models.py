from django.conf import settings
from django.db import models
from django.utils import timezone


class PlanningLevel(models.TextChoices):
    """Enumeration for the different planning levels."""

    TEACHER = "TEACHER", "Nivel Docente"
    CLASSROOM = "CLASSROOM", "Nivel Aula"


class PlanningSheet(models.Model):
    """Represents a planning sheet used by teachers or classroom level.

    A planning sheet stores structural information such as:
    - level (teacher or classroom)
    - title and description
    - sheet type and context (grade, area, school year)
    - a JSON schema describing the columns used by the frontend grid
    """

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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return the planning sheet title as its string representation."""

        return self.title


class PlanningRow(models.Model):
    """Represents a single row inside a planning sheet.

    Each row contains:
    - an index indicating its position
    - a JSON payload with the row data
    """

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
        """Return a readable representation combining sheet title and row index."""

        return f"{self.sheet.title} - row {self.index}"
