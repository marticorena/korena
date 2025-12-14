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

from apps.core.endpoints.permissions import IsAuthenticatedRest
from apps.core.endpoints.utils import graphql_style_error_response
from apps.core.messages import ERROR_MESSAGES
from apps.documents.api.serializers import DocumentVersionSerializer
from apps.documents.models import Document, DocumentVersion


class DocumentVersionUploadView(APIView):
    """Upload a new document version with GraphQL-like errors."""

    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = (JWTAuthentication,)
    permission_classes = [IsAuthenticatedRest]

    graphql_path = ["documentVersionUpload"]

    def handle_exception(self, exc: Exception) -> Response:
        """Normalize auth/permission errors to a GraphQL-like error payload."""
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):

            return graphql_style_error_response(
                message=ERROR_MESSAGES["auth.not_authenticated"],
                status_code=status.HTTP_403_FORBIDDEN,
                path=self.graphql_path,
            )

        if isinstance(exc, PermissionDenied):

            return graphql_style_error_response(
                message=ERROR_MESSAGES["auth.not_authenticated"],
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
        """Handle a new document version upload."""
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

        version = DocumentVersion.objects.create(
            document=document,
            file=uploaded_file,
        )

        document.current_version = version
        document.save(update_fields=["current_version", "updated_at"])

        serializer = DocumentVersionSerializer(version)
        payload: Dict[str, Any] = {
            "document_id": document.id,
            "version": serializer.data,
        }

        return Response(payload, status=status.HTTP_201_CREATED)
