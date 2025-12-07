from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.documents.models.abstracts import (
    DocumentVersioningMetadata,
    FileMetadata,
    NormativeDocumentMetadata,
)
from apps.documents.models.choices import DocumentLevel, DocumentVersionStatus
from apps.documents.validators import validate_pdf_or_docx
from apps.documents_ai.models.abstracts import (
    DocumentProcessingMetadata,
    DocumentStructuredContentMetadata,
)


class DocumentCategory(models.Model):
    """Configuration category describing a family of documents.

    A category defines metadata and constraints used across documents,
    such as level (state, school, teacher, classroom) and whether it is
    an official MINEDU-related document.
    """

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    level = models.CharField(
        max_length=20,
        choices=DocumentLevel.choices,
    )

    is_official = models.BooleanField(
        default=False,
        help_text=(
            "Marcar como verdadero cuando esta categoría corresponda "
            "a normas oficiales del MINEDU/Estado."
        ),
    )

    minedu_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text=(
            "Referencia opcional usada por el MINEDU "
            "(familia, grupo, código interno)."
        ),
    )

    class Meta:
        ordering = ["level", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_level_display()})"


class Document(DocumentVersioningMetadata, NormativeDocumentMetadata):
    """Main document entity.

    Represents a document from the State, School, Teacher or Classroom levels.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Usuario propietario del documento.",
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Colegio asociado al documento, si aplica.",
    )

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
        help_text="Categoría o familia del documento.",
    )

    title = models.CharField(
        max_length=255,
        help_text="Título del documento.",
    )

    description = models.TextField(
        blank=True,
        help_text="Descripción o notas internas.",
    )

    class Meta(DocumentVersioningMetadata.Meta):
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_official(self) -> bool:
        """Whether this document belongs to an official MINEDU category.

        Returns:
            bool: True when the category is marked as official.
        """

        return self.category.is_official


class DocumentVersion(
    FileMetadata,
    DocumentProcessingMetadata,
    DocumentStructuredContentMetadata,
):
    """Represents a single version of a document.

    Each version keeps:
    - the original file,
    - a structured JSON representation (blocks) used as source of truth.
    """

    def _document_file_path(instance: "DocumentVersion", filename: str) -> str:
        """Generate the upload path for files.

        Args:
            instance: DocumentVersion instance.
            filename: Original filename.

        Returns:
            str: Relative path where the file will be stored.
        """
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
        help_text="Archivo original (PDF o DOCX).",
    )

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
        help_text="Usuario que creó esta versión.",
    )

    created_at = models.DateTimeField(default=timezone.now)

    source = models.CharField(
        max_length=20,
        choices=(
            ("UPLOAD", "Subida por usuario"),
            ("GENERATED", "Generada por IA"),
            ("CRAWLED", "Obtenida desde fuente oficial"),
        ),
        default="UPLOAD",
        help_text="Origen de esta versión.",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.document.title} v{self.pk} [{self.status}]"
