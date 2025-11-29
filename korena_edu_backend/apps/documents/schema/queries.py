from typing import Optional

import graphene
from graphql import GraphQLError, GraphQLResolveInfo
from graphql_jwt.decorators import login_required

from apps.accounts.schema.decorators import verified_required
from apps.core.messages import ERROR_MESSAGES
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel
from apps.documents.schema.types import DocumentType


class DocumentQueries(graphene.ObjectType):
    """GraphQL queries related to documents."""

    my_documents = graphene.List(
        DocumentType,
        level=graphene.Argument(
            graphene.String,
            required=False,
            description=(
                "Filtrar por nivel de documento (STATE, SCHOOL, TEACHER, CLASSROOM)."
            ),
        ),
    )
    document = graphene.Field(
        DocumentType,
        id=graphene.ID(required=True),
    )

    @login_required
    @verified_required
    def resolve_my_documents(
        self,
        info: GraphQLResolveInfo,
        level: Optional[str] = None,
        **kwargs: object,
    ) -> list[DocumentModel]:
        """Return the list of documents owned by the authenticated user.

        Args:
            info (GraphQLResolveInfo): GraphQL resolver info.
            level (Optional[str]): Optional document level filter.
            **kwargs: Additional resolver arguments.

        Raises:
            GraphQLError: If level is invalid.

        Returns:
            list[DocumentModel]: Documents owned by the current user.
        """
        user = info.context.user

        queryset = DocumentModel.objects.filter(owner=user, is_archived=False)

        if level:
            if level not in DocumentLevel.values:
                raise GraphQLError(ERROR_MESSAGES["documents.invalid_level"])

            queryset = queryset.filter(type__level=level)

        return list(queryset)

    @login_required
    @verified_required
    def resolve_document(
        self,
        info: GraphQLResolveInfo,
        id: str,
        **kwargs: object,
    ) -> Optional[DocumentModel]:
        """Return a single document owned by the authenticated user.

        Args:
            info (GraphQLResolveInfo): GraphQL resolver info.
            id (str): Document primary key.
            **kwargs: Additional resolver arguments.

        Raises:
            GraphQLError: If document does not exist or is not owned by the user.

        Returns:
            Optional[DocumentModel]: The requested document.
        """
        user = info.context.user

        try:
            document = DocumentModel.objects.get(pk=id, owner=user, is_archived=False)
        except DocumentModel.DoesNotExist as exc:
            raise GraphQLError(
                ERROR_MESSAGES["documents.not_found_or_not_owned"]
            ) from exc

        return document
