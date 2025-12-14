from rest_framework import serializers

from apps.documents.models import DocumentVersion


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions."""

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "document",
            "file",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "document",
            "created_at",
        ]
