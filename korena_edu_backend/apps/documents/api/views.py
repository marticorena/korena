from typing import Any, Dict

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.endpoints.permissions import IsAuthenticatedRest, IsVerifiedRest
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
    """Upload a new document version via REST.

    This endpoint mirrors the previous GraphQL mutation logic:
    - Validates document ownership.
    - Tracks upload duration and increments Prometheus metrics.
    - Creates a new DocumentVersion and marks it as current.
    """

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticatedRest, IsVerifiedRest]

    def post(
        self,
        request: Request,
        document_id: int,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """Handle POST request to upload a new document version.

        Args:
            request: HTTP request with multipart/form-data.
            document_id: Target document primary key.

        Returns:
            Response with the created version data or an error message.
        """
        user = request.user

        try:
            document = DocumentModel.objects.get(pk=document_id, owner=user)
        except DocumentModel.DoesNotExist:
            return Response(
                {"detail": ERROR_MESSAGES["documents.not_found_or_not_owned"]},
                status=status.HTTP_404_NOT_FOUND,
            )

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": ERROR_MESSAGES["upload.no_file"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Measure upload and version creation duration.
        with document_upload_duration_seconds.time():
            version = DocumentVersionModel.objects.create(
                document=document,
                file=uploaded_file,
                status=DocumentVersionStatus.DRAFT,
                created_by=user,
            )

            document.current_version = version
            document.save(update_fields=["current_version"])

        # Increment counters for metrics.
        document_versions_uploaded_total.inc()
        documents_by_level_total.labels(level=document.type.level).inc()

        serializer = DocumentVersionSerializer(version)
        payload: Dict[str, Any] = {
            "document_id": document.id,
            "version": serializer.data,
        }

        return Response(payload, status=status.HTTP_201_CREATED)
