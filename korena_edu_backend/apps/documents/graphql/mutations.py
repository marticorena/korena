from typing import Optional

import strawberry
from strawberry.exceptions import GraphQLError
from strawberry.types import Info

from apps.core.endpoints.permissions import IsAuthenticatedGraphql
from apps.core.messages import ERROR_MESSAGES
from apps.documents.graphql.types import DocumentCategoryType, DocumentType
from apps.documents.models import Document, DocumentCategory, DocumentLevel


@strawberry.type
class CreateDocumentPayload:
    """Payload for the createDocument mutation."""

    document: DocumentType


@strawberry.type
class CreateDocumentCategoryPayload:
    """Payload for the createDocumentCategory mutation."""

    document_category: DocumentCategoryType


def _map_document_category_model(instance: DocumentCategory) -> DocumentCategoryType:
    """Map a DocumentCategory model instance to a GraphQL type."""

    return DocumentCategoryType(
        id=str(instance.pk),
        code=instance.code,
        name=instance.name,
        description=instance.description or None,
        level=instance.level,
    )


@strawberry.type
class DocumentMutations:
    """Root mutation group for document-related operations."""

    @strawberry.mutation(
        permission_classes=[IsAuthenticatedGraphql],
        name="createDocument",
    )
    def create_document(
        self,
        info: Info,
        document_category_code: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CreateDocumentPayload:
        """Create a document shell for the authenticated user."""
        user = info.context.request.user

        try:
            category = DocumentCategory.objects.get(code=document_category_code)
        except DocumentCategory.DoesNotExist as exc:
            raise GraphQLError(ERROR_MESSAGES["documents.category_not_found"]) from exc

        existing_qs = Document.objects.filter(
            owner=user,
            category=category,
        )

        if existing_qs.exists():
            raise GraphQLError(ERROR_MESSAGES["documents.already_exists"])

        resolved_title = title or category.name
        resolved_description = description or ""

        document = Document.objects.create(
            owner=user,
            category=category,
            title=resolved_title,
            description=resolved_description,
        )

        return CreateDocumentPayload(document=document)

    @strawberry.mutation(
        permission_classes=[IsAuthenticatedGraphql],
        name="createDocumentCategory",
    )
    def create_document_category(
        self,
        info: Info,
        code: str,
        name: str,
        level: str,
        description: Optional[str] = None,
    ) -> CreateDocumentCategoryPayload:
        """Create a new document category configuration."""
        normalized_code = code.strip().lower()

        if DocumentCategory.objects.filter(code=normalized_code).exists():
            raise GraphQLError(ERROR_MESSAGES["documents.category_code_already_exists"])

        if level not in {choice[0] for choice in DocumentLevel.choices}:
            raise GraphQLError(ERROR_MESSAGES["documents.invalid_level"])

        document_category = DocumentCategory.objects.create(
            code=normalized_code,
            name=name.strip(),
            description=(description or "").strip(),
            level=level,
        )

        gql_category = _map_document_category_model(document_category)

        return CreateDocumentCategoryPayload(document_category=gql_category)
