from rest_framework import serializers

from apps.documents.models import Document, DocumentVersion


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "status",
            "file",
            "created_by",
            "created_at",
            "ai_summary",
            "page_count",
            "source",
        ]
        read_only_fields = ["created_by", "created_at", "ai_summary", "page_count", "source"]


class DocumentSerializer(serializers.ModelSerializer):
    current_version = DocumentVersionSerializer(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "description",
            "type",
            "current_version",
            "created_at",
            "updated_at",
        ]
