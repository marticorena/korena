from datetime import date, datetime
from typing import Optional

import strawberry.django

from apps.accounts.graphql.types import UserType
from apps.documents.models.documents import Document, DocumentCategory, DocumentVersion


@strawberry.django.type(DocumentCategory)
class DocumentCategoryType:
    """Configuration metadata for a document category"""

    id: strawberry.ID
    code: str
    name: str
    description: str
    level: str
    is_official: bool
    minedu_reference: str


@strawberry.django.type(DocumentVersion)
class DocumentVersionType:
    """Single version of a document."""

    id: strawberry.ID
    file: str
    status: str
    created_at: datetime
    created_by: Optional[UserType]

    # File metadata
    original_filename: str
    mime_type: str
    page_count: Optional[int]

    # IA processing metadata
    is_chunking_ready: bool
    chunking_error: str

    source: str


@strawberry.django.type(Document)
class DocumentType:
    """Main document entity with current version, category and normative metadata."""

    id: strawberry.ID
    title: str
    description: str

    # Versioning and lifecycle
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    current_version: Optional[DocumentVersionType]

    # Document category
    category: DocumentCategoryType

    # Normative metadata (mainly for STATE-level / official docs)
    official_code: str
    official_number: str
    official_year: Optional[int]
    issuing_entity: str
    official_url: str
    valid_from: Optional[date]
    valid_until: Optional[date]
    is_current: bool
