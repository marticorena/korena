from typing import List, Optional

import strawberry
from strawberry.exceptions import GraphQLError
from strawberry.types import Info

from apps.core.endpoints.permissions import IsAuthenticatedGraphql, IsVerifiedGraphql
from apps.core.messages import ERROR_MESSAGES
from apps.documents.graphql.types import DocumentType
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel


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
        """
        user = info.context.request.user

        queryset = DocumentModel.objects.filter(owner=user, is_archived=False)

        if level is not None:
            if level not in DocumentLevel.values:
                raise GraphQLError(ERROR_MESSAGES["documents.invalid_level"])

            queryset = queryset.filter(type__level=level)

        return list(queryset)

    @strawberry.field(permission_classes=[IsAuthenticatedGraphql, IsVerifiedGraphql])
    def document(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> DocumentType:
        """Return a single non-archived document owned by the authenticated user.

        Raises:
            GraphQLError: If the document does not exist or is not owned
                by the current user.
        """
        user = info.context.request.user

        try:
            document = DocumentModel.objects.get(
                pk=id,
                owner=user,
                is_archived=False,
            )
        except DocumentModel.DoesNotExist as exc:
            raise GraphQLError(
                ERROR_MESSAGES["documents.not_found_or_not_owned"],
            ) from exc

        return document
