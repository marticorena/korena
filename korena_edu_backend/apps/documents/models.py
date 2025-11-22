from django.conf import settings
from django.db import models
from django.utils import timezone


class DocumentLevel(models.TextChoices):
    STATE = "STATE", "Nivel Estado"
    SCHOOL = "SCHOOL", "Nivel Colegio"
    TEACHER = "TEACHER", "Nivel Docente"
    CLASSROOM = "CLASSROOM", "Nivel Aula"


class DocumentType(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    level = models.CharField(
        max_length=20,
        choices=DocumentLevel.choices,
    )
    is_official = models.BooleanField(default=False)
    minedu_reference = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.level})"


class Document(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    current_version = models.ForeignKey(
        "DocumentVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class DocumentVersionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Borrador"
    ACTIVE = "ACTIVE", "En uso"
    HISTORICAL = "HISTORICAL", "Histórico"


def document_file_path(instance: "DocumentVersion", filename: str) -> str:
    return (
        f"documents/{instance.document_id}/"
        f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    )


class DocumentVersion(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    file = models.FileField(upload_to=document_file_path)
    status = models.CharField(
        max_length=20,
        choices=DocumentVersionStatus.choices,
        default=DocumentVersionStatus.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_versions_created",
    )
    created_at = models.DateTimeField(default=timezone.now)

    ai_summary = models.TextField(blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=(
            ("UPLOAD", "Subida por usuario"),
            ("GENERATED", "Generada por IA"),
        ),
        default="UPLOAD",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.document.title} v{self.pk} [{self.status}]"
