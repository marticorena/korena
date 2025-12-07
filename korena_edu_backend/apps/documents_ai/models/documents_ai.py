from typing import Any, Dict, Optional

from django.db import models
from django.utils import timezone

from pgvector.django import VectorField

from apps.documents.models.documents import DocumentVersion
from apps.documents_ai.models.choices import DocumentChunkCategory


class DocumentChunk(models.Model):
    """Represents a single text chunk derived from a DocumentVersion.

    This model is the unit used for semantic search (vector index) and
    RAG-style retrieval.
    """

    version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    index = models.PositiveIntegerField(
        help_text="Índice del fragmento (basado en 0).",
    )

    content = models.TextField(
        help_text=(
            "Texto del fragmento listo para IA "
            "(párrafo, encabezado, tabla en markdown, etc.)."
        ),
    )

    chunk_type = models.CharField(
        max_length=20,
        choices=DocumentChunkCategory.choices,
        default=DocumentChunkCategory.PARAGRAPH,
        help_text="Tipo de fragmento (párrafo, tabla, encabezado, etc.).",
    )

    token_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número estimado de tokens.",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadatos opcionales (página, sección, ids de bloque, etc.).",
    )

    embedding = VectorField(
        null=True,
        blank=True,
        help_text=(
            "Vector de embedding para búsqueda semántica (pgvector). "
            "La dimensión se configura a nivel de base de datos."
        ),
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["version_id", "index"]
        unique_together = ("version", "index")

    def __str__(self) -> str:
        return f"Fragmento {self.index} de {self.version}"

    @property
    def page(self) -> Optional[int]:
        """Return the page number from metadata if present.

        Returns:
            Optional[int]: Page number or None.
        """
        page = self.metadata.get("page")

        return int(page) if page is not None else None

    def to_rag_payload(self) -> Dict[str, Any]:
        """Return a minimal payload used when building RAG contexts.

        Returns:
            Dict[str, Any]: Dictionary with content and basic metadata.
        """
        payload: Dict[str, Any] = {
            "version_id": self.version_id,
            "chunk_index": self.index,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "metadata": self.metadata,
        }

        return payload
