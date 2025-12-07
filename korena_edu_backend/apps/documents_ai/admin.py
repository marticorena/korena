from django.contrib import admin

from apps.documents_ai.models.documents_ai import DocumentChunk


class DocumentChunkInline(admin.TabularInline):
    """Inline view of chunks inside a DocumentVersion."""

    model = DocumentChunk
    extra = 0

    fields = (
        "index",
        "chunk_type",
        "token_count",
        "page_display",
        "created_at",
    )
    readonly_fields = (
        "index",
        "chunk_type",
        "token_count",
        "page_display",
        "created_at",
    )
    ordering = ("index",)

    def page_display(self, obj: DocumentChunk) -> str:
        """Return a human-friendly page number from metadata."""
        page = obj.page
        return str(page) if page is not None else "-"

    page_display.short_description = "Página"


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin configuration for document chunks."""

    list_display = (
        "id",
        "version",
        "index",
        "chunk_type",
        "page_display",
        "token_count",
        "has_embedding",
        "created_at",
    )
    list_filter = (
        "chunk_type",
        "version__document",
        "version__status",
        "version__source",
        "created_at",
    )
    search_fields = (
        "content",
        "version__document__title",
    )
    autocomplete_fields = ("version",)
    ordering = ("version_id", "index")
    list_select_related = ("version", "version__document")

    readonly_fields = (
        "created_at",
        "embedding",
    )

    def page_display(self, obj: DocumentChunk) -> str:
        """Return a human-friendly page number from metadata."""
        page = obj.page
        return str(page) if page is not None else "-"

    page_display.short_description = "Página"

    def has_embedding(self, obj: DocumentChunk) -> bool:
        """Return True when the chunk already has an embedding."""
        return obj.embedding is not None

    has_embedding.boolean = True
    has_embedding.short_description = "Embedding"
