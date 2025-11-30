from django.conf import settings
from django.db import models
from django.utils import timezone


class DocumentLevel(models.TextChoices):
    """Enumeration of all supported document levels."""

    STATE = "STATE", "Nivel Estado"
    SCHOOL = "SCHOOL", "Nivel Colegio"
    TEACHER = "TEACHER", "Nivel Docente"
    CLASSROOM = "CLASSROOM", "Nivel Aula"


class DocumentVersionStatus(models.TextChoices):
    """Enumeration of possible states for a document version."""

    DRAFT = "DRAFT", "Borrador"
    ACTIVE = "ACTIVE", "En uso"
    HISTORICAL = "HISTORICAL", "Histórico"


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
        help_text="Marcar como verdadero cuando esta categoría corresponda "
        "a normas oficiales del MINEDU/Estado.",
    )

    minedu_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Referencia opcional usada por el MINEDU (familia, grupo, código interno).",
    )

    class Meta:
        ordering = ["level", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_level_display()})"


class DocumentVersioningMetadata(models.Model):
    """Abstract base with versioning and lifecycle information.

    Used by `Document` to track:
    - current active version
    - archived state
    - timestamps
    """

    current_version = models.ForeignKey(
        "DocumentVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Versión actualmente marcada como 'En uso'.",
    )

    is_archived = models.BooleanField(
        default=False,
        help_text="Si está activo, el documento se mantiene solo como histórico "
        "y se oculta de los flujos activos.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NormativeDocumentMetadata(models.Model):
    """Abstract base for normative/official document metadata."""

    official_code = models.CharField(
        max_length=100,
        blank=True,
        help_text='Código corto de la norma, por ejemplo: "Ley 28044", "DS 011-2012-ED".',
    )
    official_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Número oficial completo, por ejemplo: "RVM N° 123-2024-MINEDU".',
    )
    official_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Año de publicación de la norma.",
    )
    issuing_entity = models.CharField(
        max_length=150,
        blank=True,
        help_text='Entidad emisora, por ejemplo: "MINEDU", "Congreso", "DRE Cusco".',
    )
    official_url = models.URLField(
        blank=True,
        help_text="URL a la publicación oficial (gob.pe, El Peruano, MINEDU).",
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha desde la cual el documento se considera vigente.",
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha hasta la cual el documento es válido, si aplica.",
    )
    is_current = models.BooleanField(
        default=True,
        help_text="Indica si esta norma se considera la referencia vigente.",
    )

    class Meta:
        abstract = True


class FileMetadata(models.Model):
    """Abstract base with original file metadata."""

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nombre original del archivo subido o descargado.",
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tipo MIME detectado (application/pdf, docx, etc.).",
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="Checksum opcional (SHA-256) para detectar duplicados.",
    )
    page_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número de páginas para formatos paginados.",
    )
    language = models.CharField(
        max_length=10,
        blank=True,
        help_text="Idioma predominante (ej. 'es', 'qu').",
    )

    class Meta:
        abstract = True


class AIProcessingMetadata(models.Model):
    """Abstract base with IA-related processing metadata."""

    extracted_text = models.TextField(
        blank=True,
        help_text="Texto plano extraído del archivo original.",
    )

    extracted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se extrajo el texto.",
    )

    ai_summary = models.TextField(
        blank=True,
        help_text="Resumen generado por IA.",
    )

    is_indexed = models.BooleanField(
        default=False,
        help_text="Verdadero cuando la versión ha sido troceada e indexada para IA.",
    )

    indexing_error = models.TextField(
        blank=True,
        help_text="Mensaje de error si falló el chunking/indexación.",
    )

    class Meta:
        abstract = True


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

    def __str__(self):
        return self.title

    @property
    def is_official(self) -> bool:
        """Whether this document belongs to an official MINEDU category."""
        return self.category.is_official


def document_file_path(instance: "DocumentVersion", filename: str) -> str:
    """Generate the upload path for files."""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"documents/{instance.document_id}/{timestamp}_{filename}"


class DocumentVersion(FileMetadata, AIProcessingMetadata):
    """Represents a single version of a document."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    file = models.FileField(
        upload_to=document_file_path,
        help_text="Archivo original (PDF, DOCX, etc.).",
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

    def __str__(self):
        return f"{self.document.title} v{self.pk} [{self.status}]"


class DocumentChunk(models.Model):
    """Represents a single text chunk derived from a DocumentVersion."""

    version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    index = models.PositiveIntegerField(
        help_text="Índice del fragmento (basado en 0).",
    )

    content = models.TextField(
        help_text="Texto del fragmento.",
    )

    token_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número estimado de tokens.",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadatos opcionales (páginas, secciones, etc.).",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["version_id", "index"]
        unique_together = ("version", "index")

    def __str__(self):
        return f"Fragmento {self.index} de {self.version}"
