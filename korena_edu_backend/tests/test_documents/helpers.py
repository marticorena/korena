from django.contrib.auth import get_user_model

from apps.documents.models.documents import Document, DocumentCategory, DocumentLevel

User = get_user_model()


def helper_test_create_document_category(
    level: str = DocumentLevel.TEACHER,
) -> DocumentCategory:
    """Create a DocumentCategory for tests."""
    category = DocumentCategory.objects.create(
        code=f"doc-{level.lower()}",
        name=f"Documento {level}",
        description="Tipo de prueba",
        level=level,
        is_official=False,
    )

    return category


def helper_test_create_document(
    owner: User,
    category: DocumentCategory,
    title: str = "Documento de prueba",
    description: str = "Descripción",
) -> Document:
    """Create a Document for tests."""
    document = Document.objects.create(
        owner=owner,
        school=None,
        category=category,
        title=title,
        description=description,
        is_archived=False,
    )

    return document
