from typing import Any, Dict

from rest_framework import serializers

from apps.documents.models import DocumentVersion as DocumentVersionModel


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions."""

    class Meta:
        model = DocumentVersionModel
        fields = [
            "id",
            "document",
            "file",
            "status",
            "created_by",
            "created_at",
            "ai_summary",
            "page_count",
            "source",
        ]

    def to_representation(self, instance: DocumentVersionModel) -> Dict[str, Any]:
        """Return the serialized representation.

        Args:
            instance: DocumentVersion instance.

        Returns:
            Serialized data as a dict.
        """
        data = super().to_representation(instance)

        return data
