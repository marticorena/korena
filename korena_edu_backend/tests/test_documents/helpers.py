from django.contrib.auth import get_user_model

from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel
from apps.documents.models import DocumentType as DocumentTypeModel

User = get_user_model()


def create_document_type(level: str = DocumentLevel.TEACHER) -> DocumentTypeModel:
    """Create a DocumentType for tests."""
    doc_type = DocumentTypeModel.objects.create(
        code=f"doc-{level.lower()}",
        name=f"Documento {level}",
        description="Tipo de prueba",
        level=level,
        is_official=False,
    )

    return doc_type


def create_document(
    owner: User,
    doc_type: DocumentTypeModel,
    title: str = "Documento de prueba",
    description: str = "Descripción",
) -> DocumentModel:
    """Create a Document for tests."""
    document = DocumentModel.objects.create(
        owner=owner,
        school=None,
        type=doc_type,
        title=title,
        description=description,
        is_archived=False,
    )

    return document
