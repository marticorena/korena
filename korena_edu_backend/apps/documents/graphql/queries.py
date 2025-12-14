from typing import List, Optional

import strawberry
from strawberry.exceptions import GraphQLError
from strawberry.types import Info

from apps.core.endpoints.permissions import IsAuthenticatedGraphql, IsVerifiedGraphql
from apps.core.messages import ERROR_MESSAGES
from apps.documents.graphql.types import DocumentType
from apps.documents.models import Document, DocumentLevel


@strawberry.type
class DocumentQueries:
    """Document-related GraphQL queries."""

    @strawberry.field(permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql])
    def my_documents(
        self,
        info: Info,
        level: Optional[str] = None,
    ) -> List[DocumentType]:
        """Return non-archived documents for the authenticated user.

        Optionally filtered by document level.

        Args:
            info: GraphQL resolver context.
            level: Optional document level filter (STATE, SCHOOL, TEACHER, CLASSROOM).

        Returns:
            List[DocumentType]: List of document GraphQL types.

        Raises:
            GraphQLError: If an invalid level string is provided.
        """
        user = info.context.request.user

        queryset = Document.objects.filter(owner=user, is_archived=False)

        if level is not None:
            if level not in DocumentLevel.values:
                raise GraphQLError(ERROR_MESSAGES["documents.invalid_level"])

            queryset = queryset.filter(category__level=level)

        return list(queryset)

    @strawberry.field(permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql])
    def document(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> DocumentType:
        """Return a single non-archived document owned by the authenticated user.

        Args:
            info: GraphQL resolver context.
            id: ID of the document.

        Returns:
            DocumentType: The requested document.

        Raises:
            GraphQLError: If the document does not exist or is not owned by the user.
        """
        user = info.context.request.user

        try:
            document = Document.objects.get(
                pk=id,
                owner=user,
                is_archived=False,
            )
        except Document.DoesNotExist as exc:
            raise GraphQLError(
                ERROR_MESSAGES["documents.not_found_or_not_owned"],
            ) from exc

        return document
