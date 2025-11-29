import graphene
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError, GraphQLResolveInfo
from graphql_jwt.decorators import login_required

from apps.accounts.schema.decorators import verified_required
from apps.core.messages import ERROR_MESSAGES
from apps.core.metrics import (
    document_upload_duration_seconds,
    document_versions_uploaded_total,
    documents_by_level_total,
    track_graphql_operation,
)
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentVersion as DocumentVersionModel
from apps.documents.models import DocumentVersionStatus
from apps.documents.schema.types import DocumentType, DocumentVersionType


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

    @track_graphql_operation("upload_document_version")
    @login_required
    @verified_required
    def mutate(
        self,
        info: GraphQLResolveInfo,
        document_id: str,
        file: Upload,
        **kwargs: object,
    ) -> "UploadDocumentVersion":
        """Create a new version and set it as the current version.

        Args:
            info: Resolver info including request context.
            document_id: Target document ID.
            file: Uploaded file object.
            **kwargs: Additional arguments.

        Raises:
            GraphQLError: If the document does not exist or does not belong
                to the authenticated user.

        Returns:
            UploadDocumentVersion: Mutation result with new version and document.
        """
        user = info.context.user

        try:
            document = DocumentModel.objects.get(pk=document_id, owner=user)
        except DocumentModel.DoesNotExist as exc:
            raise GraphQLError(
                ERROR_MESSAGES["documents.not_found_or_not_owned"]
            ) from exc

        # Measure upload and version creation duration.
        with document_upload_duration_seconds.time():
            version = DocumentVersionModel.objects.create(
                document=document,
                file=file,
                status=DocumentVersionStatus.DRAFT,
                created_by=user,
            )

            document.current_version = version
            document.save(update_fields=["current_version"])

        # Increment counters for metrics.
        document_versions_uploaded_total.inc()
        documents_by_level_total.labels(level=document.type.level).inc()

        return UploadDocumentVersion(document_version=version, document=document)


class DocumentMutations(graphene.ObjectType):
    """Root mutation group for document-related operations."""

    upload_document_version = UploadDocumentVersion.Field()
