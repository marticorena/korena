from django.db import models


class DocumentChunkCategory(models.TextChoices):
    """Category of chunk used for IA and search."""

    PARAGRAPH = "PARAGRAPH", "Párrafo"
    HEADING = "HEADING", "Encabezado"
    TABLE = "TABLE", "Tabla"
    LIST = "LIST", "Lista"
    OTHER = "OTHER", "Otro"
