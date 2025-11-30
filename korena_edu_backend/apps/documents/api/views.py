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
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentVersion as DocumentVersionModel
from apps.documents.models import DocumentVersionStatus


class DocumentVersionUploadView(APIView):
    """REST endpoint to upload a new document version with GraphQL-like errors."""

    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = (JWTAuthentication,)
    permission_classes = [IsAuthenticatedRest, IsVerifiedRest]

    graphql_path = ["documentVersionUpload"]

    def handle_exception(self, exc: Exception) -> Response:
        """Normalize auth/permission errors to a GraphQL-like error payload."""
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
        user = request.user

        try:
            document = DocumentModel.objects.get(pk=document_id, owner=user)
        except DocumentModel.DoesNotExist:
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

        with document_upload_duration_seconds.time():
            version = DocumentVersionModel.objects.create(
                document=document,
                file=uploaded_file,
                status=DocumentVersionStatus.DRAFT,
                created_by=user,
            )
            document.current_version = version
            document.save(update_fields=["current_version"])

        document_versions_uploaded_total.inc()
        documents_by_level_total.labels(level=document.type.level).inc()

        serializer = DocumentVersionSerializer(version)
        payload: Dict[str, Any] = {
            "document_id": document.id,
            "version": serializer.data,
        }

        # Success stays as plain JSON payload (no GraphQL envelope).
        return Response(payload, status=status.HTTP_201_CREATED)
