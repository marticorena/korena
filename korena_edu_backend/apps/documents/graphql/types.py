from datetime import datetime
from typing import Optional

import strawberry.django

from apps.documents.models import Document, DocumentCategory, DocumentVersion


@strawberry.django.type(DocumentCategory)
class DocumentCategoryType:
    """Configuration metadata for a document category."""

    id: strawberry.ID
    code: str
    name: str
    description: str
    level: str


@strawberry.django.type(DocumentVersion)
class DocumentVersionType:
    """Single uploaded file for a document."""

    id: strawberry.ID
    file: str
    created_at: datetime


@strawberry.django.type(Document)
class DocumentType:
    """Main document entity with current version and category."""

    id: strawberry.ID
    title: str
    description: str

    is_archived: bool
    created_at: datetime
    updated_at: datetime

    current_version: Optional[DocumentVersionType]
    category: DocumentCategoryType
