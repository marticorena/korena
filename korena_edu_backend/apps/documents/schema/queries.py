from typing import Optional

import graphene
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel
from apps.documents.schema.types import DocumentType
from graphql import GraphQLError, GraphQLResolveInfo


class DocumentQueries(graphene.ObjectType):
    """GraphQL queries related to documents."""

    my_documents = graphene.List(
        DocumentType,
        level=graphene.Argument(
            graphene.String,
            required=False,
            description="Filtrar por nivel de documento (STATE, SCHOOL, TEACHER, CLASSROOM).",
        ),
    )
    document = graphene.Field(
        DocumentType,
        id=graphene.ID(required=True),
    )

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
            GraphQLError: If the user is not authenticated.

        Returns:
            list[DocumentModel]: Documents owned by the current user.
        """
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Debes iniciar sesión para ver tus documentos.")

        queryset = DocumentModel.objects.filter(owner=user, is_archived=False)

        if level:
            if level not in DocumentLevel.values:
                raise GraphQLError("El nivel de documento proporcionado no es válido.")

            queryset = queryset.filter(type__level=level)

        return list(queryset)

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
            GraphQLError: If the user is not authenticated.

        Returns:
            Optional[DocumentModel]: The document if it exists and belongs to the user.
        """
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Debes iniciar sesión para ver este documento.")

        try:
            document = DocumentModel.objects.get(pk=id, owner=user, is_archived=False)
        except DocumentModel.DoesNotExist:
            return None

        return document
