from typing import Any, Dict

from rest_framework import serializers

from apps.documents.models import DocumentVersion


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions.

    This serializer exposes both user-visible fields (file, status)
    and internal metadata fields that are useful for inspection and
    debugging (indexing flags, file metadata). The extracted_text field
    is intentionally omitted to avoid sending large payloads.
    """

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "document",
            "file",
            "status",
            "created_by",
            "created_at",
            "source",
            # File metadata (FileMetadata mixin)
            "original_filename",
            "mime_type",
            "checksum",
            "page_count",
            "language",
            # IA processing metadata (AIProcessingMetadata mixin)
            "ai_summary",
            "is_indexed",
            "indexing_error",
            "extracted_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "source",
            "original_filename",
            "mime_type",
            "checksum",
            "page_count",
            "language",
            "ai_summary",
            "is_indexed",
            "indexing_error",
            "extracted_at",
        ]

    def to_representation(self, instance: DocumentVersion) -> Dict[str, Any]:
        """Return the serialized representation.

        Args:
            instance: DocumentVersion instance.

        Returns:
            Serialized data as a dict.
        """
        data = super().to_representation(instance)

        return data
