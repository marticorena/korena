from datetime import datetime
from typing import Optional

import strawberry.django

from apps.accounts.graphql.types import UserType
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentType as DocumentTypeModel
from apps.documents.models import DocumentVersion as DocumentVersionModel


@strawberry.django.type(DocumentTypeModel)
class DocumentTypeConfig:
    """Configuration metadata for a document type."""

    id: strawberry.ID
    code: str
    name: str
    description: str
    level: str
    is_official: bool
    minedu_reference: str


@strawberry.django.type(DocumentVersionModel)
class DocumentVersionType:
    """Single version of a document."""

    id: strawberry.ID
    file: str
    status: str
    created_at: datetime
    ai_summary: str
    page_count: Optional[int]
    source: str
    created_by: Optional[UserType]


@strawberry.django.type(DocumentModel)
class DocumentType:
    """Main document entity with current version and type."""

    id: strawberry.ID
    title: str
    description: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    type: DocumentTypeConfig
    current_version: Optional[DocumentVersionType]
