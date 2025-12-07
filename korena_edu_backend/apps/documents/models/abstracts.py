from django.db import models
from django.utils import timezone


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
        help_text=(
            "Si está activo, el documento se mantiene solo como histórico "
            "y se oculta de los flujos activos."
        ),
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
        help_text=(
            'Código corto de la norma, por ejemplo: "Ley 28044", ' '"DS 011-2012-ED".'
        ),
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

    class Meta:
        abstract = True
