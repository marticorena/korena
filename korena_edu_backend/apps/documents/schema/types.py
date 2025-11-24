import graphene
from apps.documents.models import Document as DocumentModel
from apps.documents.models import DocumentType as DocumentTypeModel
from apps.documents.models import DocumentVersion as DocumentVersionModel
from graphene_django import DjangoObjectType


class DocumentTypeType(DjangoObjectType):
    """GraphQL type representing the document type configuration."""

    class Meta:
        model = DocumentTypeModel
        fields = (
            "id",
            "code",
            "name",
            "description",
            "level",
            "is_official",
            "minedu_reference",
        )


class DocumentVersionType(DjangoObjectType):
    """GraphQL type representing a single version of a document."""

    class Meta:
        model = DocumentVersionModel
        fields = (
            "id",
            "file",
            "status",
            "created_by",
            "created_at",
            "ai_summary",
            "page_count",
            "source",
        )


class DocumentType(DjangoObjectType):
    """GraphQL type representing a document with its current version."""

    type = graphene.Field(DocumentTypeType)
    current_version = graphene.Field(DocumentVersionType)

    class Meta:
        model = DocumentModel
        fields = (
            "id",
            "owner",
            "school",
            "type",
            "title",
            "description",
            "current_version",
            "is_archived",
            "created_at",
            "updated_at",
        )
