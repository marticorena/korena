from typing import List, Optional

import strawberry
from strawberry.types import Info

from apps.core.graphql.permissions import IsAuthenticated, IsVerified
from apps.core.messages import ERROR_MESSAGES
from apps.documents.graphql.types import DocumentType
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel


@strawberry.type
class DocumentQueries:
    """Document-related GraphQL queries."""

    @strawberry.field(permission_classes=[IsAuthenticated, IsVerified])
    def my_documents(
        self,
        info: Info,
        level: Optional[str] = None,
    ) -> List[DocumentType]:
        user = info.context.request.user

        queryset = DocumentModel.objects.filter(owner=user, is_archived=False)

        if level:
            if level not in DocumentLevel.values:
                raise ValueError(ERROR_MESSAGES["documents.invalid_level"])

            queryset = queryset.filter(type__level=level)

        return list(queryset)

    @strawberry.field(permission_classes=[IsAuthenticated, IsVerified])
    def document(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> Optional[DocumentType]:
        user = info.context.request.user

        try:
            document = DocumentModel.objects.get(
                pk=id,
                owner=user,
                is_archived=False,
            )
        except DocumentModel.DoesNotExist as exc:
            raise ValueError(
                ERROR_MESSAGES["documents.not_found_or_not_owned"],
            ) from exc

        return document
