from typing import Any, Dict

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.endpoints.permissions import IsAuthenticatedRest, IsVerifiedRest
from apps.core.endpoints.utils import graphql_style_error_response
from apps.core.messages import ERROR_MESSAGES
from apps.core.metrics import (
    document_upload_duration_seconds,
    document_versions_uploaded_total,
    documents_by_level_total,
)
from apps.documents.api.serializers import DocumentVersionSerializer
from apps.documents.models.documents import (
    Document,
    DocumentVersion,
    DocumentVersionStatus,
)


class DocumentVersionUploadView(APIView):
    """REST endpoint to upload a new document version with GraphQL-like errors.

    This view accepts a multipart/form-data request with a single `file`
    field and creates a new DocumentVersion associated with the given
    document_id, updating the document.current_version pointer.
    """

    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = (JWTAuthentication,)
    permission_classes = [IsAuthenticatedRest, IsVerifiedRest]

    graphql_path = ["documentVersionUpload"]

    def handle_exception(self, exc: Exception) -> Response:
        """Normalize auth/permission errors to a GraphQL-like error payload.

        Args:
            exc: Exception raised by the view.

        Returns:
            Response: DRF response with a GraphQL-like error envelope.
        """
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            return graphql_style_error_response(
                message=ERROR_MESSAGES.get(
                    "auth.not_authenticated",
                    "No autenticado.",
                ),
                status_code=status.HTTP_403_FORBIDDEN,
                path=self.graphql_path,
            )

        if isinstance(exc, PermissionDenied):
            return graphql_style_error_response(
                message=ERROR_MESSAGES.get(
                    "auth.not_verified",
                    "Cuenta no verificada.",
                ),
                status_code=status.HTTP_403_FORBIDDEN,
                path=self.graphql_path,
            )

        return super().handle_exception(exc)

    def post(
        self,
        request: Request,
        document_id: int,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """Handle a new document version upload.

        Args:
            request: Incoming HTTP request.
            document_id: ID of the Document that will receive the new version.

        Returns:
            Response: Serialized DocumentVersion data or GraphQL-like error.
        """
        user = request.user

        try:
            document = Document.objects.get(pk=document_id, owner=user)
        except Document.DoesNotExist:
            return graphql_style_error_response(
                message=ERROR_MESSAGES["documents.not_found_or_not_owned"],
                status_code=status.HTTP_404_NOT_FOUND,
                path=self.graphql_path,
                code="BAD_USER_INPUT",
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return graphql_style_error_response(
                message=ERROR_MESSAGES["upload.no_file"],
                status_code=status.HTTP_400_BAD_REQUEST,
                path=self.graphql_path,
                code="BAD_USER_INPUT",
            )

        # Extract basic file metadata from the uploaded file.
        original_filename = getattr(uploaded_file, "name", "")
        mime_type = getattr(uploaded_file, "content_type", "") or ""

        with document_upload_duration_seconds.time():
            # Create the new version as DRAFT; promotion to ACTIVE can be
            # handled in a separate flow if needed.
            version = DocumentVersion.objects.create(
                document=document,
                file=uploaded_file,
                status=DocumentVersionStatus.DRAFT,
                created_by=user,
                original_filename=original_filename,
                mime_type=mime_type,
                # page_count, language, checksum, extracted_text, etc.
                # will be filled later by background processing.
            )

            # Update the current_version pointer to this new version.
            document.current_version = version
            document.save(update_fields=["current_version", "updated_at"])

        # Metrics: count uploaded versions and documents per level.
        document_versions_uploaded_total.inc()
        documents_by_level_total.labels(level=document.category.level).inc()

        serializer = DocumentVersionSerializer(version)
        payload: Dict[str, Any] = {
            "document_id": document.id,
            "version": serializer.data,
        }

        # Success stays as plain JSON payload (no GraphQL envelope).
        return Response(payload, status=status.HTTP_201_CREATED)
