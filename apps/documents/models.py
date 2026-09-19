from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.documents.validators import validate_pdf_or_docx


class DocumentLevel(models.TextChoices):
    """High-level ownership / scope of a document."""

    STATE = "STATE", "Nivel Estado"
    SCHOOL = "SCHOOL", "Nivel Colegio"
    TEACHER = "TEACHER", "Nivel Docente"
    CLASSROOM = "CLASSROOM", "Nivel Aula"


class DocumentCategory(models.Model):
    """A configurable document family/category."""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    level = models.CharField(
        max_length=20,
        choices=DocumentLevel.choices,
    )

    class Meta:
        ordering = ["level", "name"]

    def __str__(self) -> str:

        return f"{self.name} ({self.get_level_display()})"


class Document(models.Model):
    """Main document entity."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Document owner.",
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="School context when applicable (e.g. SCHOOL/CLASSROOM).",
    )

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
        help_text="Document category/family.",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    current_version = models.ForeignKey(
        "documents.DocumentVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Currently active version used by the system.",
    )

    is_archived = models.BooleanField(
        default=False,
        help_text="Whether the document is archived and excluded from active flows.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:

        return self.title


class DocumentVersion(models.Model):
    """Represents an uploaded file for a document."""

    def _document_file_path(instance: "DocumentVersion", filename: str) -> str:
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")

        return f"documents/{instance.document_id}/{timestamp}_{filename}"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    file = models.FileField(
        upload_to=_document_file_path,
        validators=[validate_pdf_or_docx],
        help_text="Original file (PDF or DOCX).",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:

        return f"{self.document.title} v{self.pk}"
