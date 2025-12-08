from django.db import models


class DocumentStructuredContentMetadata(models.Model):
    """Structured content metadata for a document version."""

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
    """Processing metadata for chunking and embeddings."""

    ai_summary = models.TextField(
        blank=True,
        help_text="Resumen generado por IA.",
    )

    chunking_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se generaron los fragmentos por última vez.",
    )

    is_chunking_ready = models.BooleanField(
        default=False,
        help_text="Verdadero cuando se generaron correctamente los fragmentos.",
    )

    chunking_error = models.TextField(
        blank=True,
        help_text="Mensaje de error si falló el proceso de chunking.",
    )

    embeddings_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se generaron los embeddings por última vez.",
    )

    is_embeddings_ready = models.BooleanField(
        default=False,
        help_text="Verdadero cuando todos los fragmentos tienen embeddings.",
    )

    embeddings_error = models.TextField(
        blank=True,
        help_text="Mensaje de error si falló la generación de embeddings.",
    )

    class Meta:
        abstract = True
