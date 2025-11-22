"""REST API endpoints for managing documents and their versions."""

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils import timezone

from apps.documents.models import Document, DocumentVersion, DocumentVersionStatus
from apps.documents.serializers import DocumentVersionSerializer, DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    """Provide CRUD operations for documents scoped to the authenticated user."""

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the documents owned by the request user."""
        # Only user's documents by default

        return Document.objects.filter(owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="upload-version")
    def upload_version(self, request, pk=None):
        """Create a new document version from the uploaded file and mark it current."""
        document = self.get_object()
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file provided."}, status=400)

        version = DocumentVersion.objects.create(
            document=document,
            file=file_obj,
            status=DocumentVersionStatus.DRAFT,
            created_by=request.user,
            created_at=timezone.now(),
        )
        # Set as current_version
        document.current_version = version
        document.save(update_fields=["current_version"])

        serializer = DocumentVersionSerializer(version)

        return Response(serializer.data, status=201)
