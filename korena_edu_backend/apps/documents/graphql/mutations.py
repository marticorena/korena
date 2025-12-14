from typing import Optional

import strawberry
from strawberry.exceptions import GraphQLError
from strawberry.types import Info

from apps.core.endpoints.permissions import IsAuthenticatedGraphql, IsVerifiedGraphql
from apps.core.messages import ERROR_MESSAGES
from apps.documents.graphql.types import DocumentCategoryType, DocumentType
from apps.documents.models.documents import Document, DocumentCategory


@strawberry.type
class CreateDocumentPayload:
    """Payload for the createDocument mutation."""

    document: DocumentType


@strawberry.type
class CreateDocumentCategoryPayload:
    """Payload for the DocumentCategoryType mutation."""

    document_category: DocumentCategoryType


def _map_document_category_model(instance: DocumentCategory) -> DocumentCategoryType:
    """Map a DocumentCategory model instance to a GraphQL type.

    Args:
        instance: DocumentCategory model instance.

    Returns:
        DocumentCategoryType: GraphQL representation.
    """

    return DocumentCategoryType(
        id=str(instance.pk),
        code=instance.code,
        name=instance.name,
        description=instance.description or None,
        level=instance.level,
        minedu_reference=instance.minedu_reference or None,
    )


@strawberry.type
class DocumentMutations:
    """Root mutation group for document-related operations.

    File uploads are handled via REST:
    - POST /api/documents/<id>/versions/  (multipart/form-data)
    """

    @strawberry.mutation(
        permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql],
        name="createDocument",
    )
    def create_document(
        self,
        info: Info,
        document_category_code: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CreateDocumentPayload:
        """Create a document shell for the authenticated user.

        This mutation creates the base document record (metadata). File
        uploads are handled separately via the REST endpoint.

        Args:
            info: GraphQL resolver info object.
            document_category_code: Code of the DocumentCategory configuration to use.
            title: Optional custom title; defaults to the category name.
            description: Optional description for this document.

        Returns:
            CreateDocumentPayload: Payload containing the created document.

        Raises:
            GraphQLError: If the category does not exist, the school is invalid,
                or the user already has a document of this category (and school).
        """
        user = info.context.request.user

        try:
            category = DocumentCategory.objects.get(code=document_category_code)
        except DocumentCategory.DoesNotExist as exc:
            raise GraphQLError(
                ERROR_MESSAGES["documents.category_not_found"],
            ) from exc

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
        permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql],
        name="createDocumentCategory",
    )
    def create_document_category(
        self,
        info: Info,
        code: str,
        name: str,
        level: str,
        description: Optional[str] = None,
        minedu_reference: Optional[str] = None,
    ) -> CreateDocumentCategoryPayload:
        """Create a new document category configuration.

        Any verified user can create new document categories so the taxonomy
        can grow organically from real usage.

        Args:
            info: GraphQL resolver info object.
            code: Unique slug-like code for this category (e.g. 'pei', 'pat', 'cneb').
            name: Human-friendly name for this document category.
            level: Level to which this category belongs (STATE, SCHOOL, TEACHER, CLASSROOM).
            description: Optional description of the category.
            minedu_reference: Optional reference used by MINEDU (family, internal code, etc.).

        Returns:
            CreateDocumentCategoryPayload: Payload containing the created category.

        Raises:
            GraphQLError: If the code already exists or the level is invalid.
        """
        # Enforce uniqueness of the code.
        if DocumentCategory.objects.filter(code=code).exists():
            raise GraphQLError(ERROR_MESSAGES["documents.category_code_already_exists"])

        try:
            document_category = DocumentCategory.objects.create(
                code=code,
                name=name,
                description=description or "",
                level=level,
                minedu_reference=minedu_reference or "",
            )
        except ValueError as exc:
            # For invalid level or other enum-related errors.
            raise GraphQLError(ERROR_MESSAGES["validation.error"]) from exc

        gql_category = _map_document_category_model(document_category)

        return CreateDocumentCategoryPayload(document_category=gql_category)
