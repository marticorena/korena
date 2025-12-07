from django.db import models


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
