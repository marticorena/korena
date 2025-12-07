from django.db import models


class DocumentStructuredContentMetadata(models.Model):
    """Abstract base with normalized structured content for a document version.

    This JSON stores the canonical representation used by search/IA and
    the processed view in the frontend.

    High-level schema example:
    {
        "blocks": [
            {"id": "b1", "type": "heading", "level": 1, "text": "...", "page": 1},
            {"id": "b2", "type": "paragraph", "text": "...", "page": 1},
            {
                "id": "t1",
                "type": "table",
                "title": "...",
                "page": 2,
                "columns": ["Col 1", "Col 2"],
                "rows": [["a", "b"], ["c", "d"]],
            },
            ...
        ]
    }
    """

    structured_content = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Representación estructurada normalizada del documento "
            "(bloques: encabezados, párrafos, tablas, listas, etc.)."
        ),
    )

    structured_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se generó o actualizó el contenido estructurado.",
    )

    is_structured_ready = models.BooleanField(
        default=False,
        help_text=(
            "Indica si el contenido estructurado está listo para ser usado "
            "en RAG y en la vista procesada."
        ),
    )

    structured_error = models.TextField(
        blank=True,
        help_text="Mensaje de error si falló el pipeline de contenido estructurado.",
    )

    class Meta:
        abstract = True


class DocumentProcessingMetadata(models.Model):
    """Abstract base with IA-related processing metadata.

    This keeps:
    - AI summary for UX / quick understanding
    - indexing flags for chunks/embeddings
    """

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
