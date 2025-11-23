from typing import Optional

import graphene
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentLevel
from apps.documents.models import DocumentType as DocumentTypeModel
from apps.documents.models import DocumentVersion as DocumentVersionModel
from apps.documents.models import DocumentVersionStatus
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError, GraphQLResolveInfo


class DocumentTypeType(DjangoObjectType):
    """GraphQL type representing the document type configuration."""

    class Meta:
        model = DocumentTypeModel
        fields = (
            "id",
            "code",
            "name",
            "description",
            "level",
            "is_official",
            "minedu_reference",
        )


class DocumentVersionType(DjangoObjectType):
    """GraphQL type representing a single version of a document."""

    class Meta:
        model = DocumentVersionModel
        fields = (
            "id",
            "file",
            "status",
            "created_by",
            "created_at",
            "ai_summary",
            "page_count",
            "source",
        )


class DocumentType(DjangoObjectType):
    """GraphQL type representing a document with its current version."""

    type = graphene.Field(DocumentTypeType)
    current_version = graphene.Field(DocumentVersionType)

    class Meta:
        model = DocumentModel
        fields = (
            "id",
            "owner",
            "school",
            "type",
            "title",
            "description",
            "current_version",
            "is_archived",
            "created_at",
            "updated_at",
        )


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


class UploadDocumentVersion(graphene.Mutation):
    """Mutation to upload a new version for an existing document.

    Creates a new DocumentVersion and marks it as the current version
    of the given document.
    """

    class Arguments:
        document_id = graphene.ID(required=True)
        file = Upload(required=True)

    document_version = graphene.Field(DocumentVersionType)
    document = graphene.Field(DocumentType)

    @classmethod
    def mutate(
        cls,
        root: Optional[object],
        info: GraphQLResolveInfo,
        document_id: str,
        file: Upload,
        **kwargs: object,
    ) -> "UploadDocumentVersion":
        """Create a new version and set it as the current version.

        Args:
            root (Optional[object]): Root resolver object (unused).
            info (GraphQLResolveInfo): Resolver info including request context.
            document_id (str): Target document ID.
            file (Upload): Uploaded file object.
            **kwargs: Additional arguments.

        Raises:
            GraphQLError: If user is not authenticated or document not found.

        Returns:
            UploadDocumentVersion: Mutation result with new version and document.
        """
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Debes iniciar sesión para subir documentos.")

        try:
            document = DocumentModel.objects.get(pk=document_id, owner=user)
        except DocumentModel.DoesNotExist as exc:
            raise GraphQLError("Documento no encontrado o no te pertenece.") from exc

        version = DocumentVersionModel.objects.create(
            document=document,
            file=file,
            status=DocumentVersionStatus.DRAFT,
            created_by=user,
        )

        document.current_version = version
        document.save(update_fields=["current_version"])

        return cls(document_version=version, document=document)


class DocumentMutations(graphene.ObjectType):
    """Root mutation group for document-related operations."""

    upload_document_version = UploadDocumentVersion.Field()
