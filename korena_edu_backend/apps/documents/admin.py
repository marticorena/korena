# apps/documents/admin.py

from django.contrib import admin

from apps.documents.models import (
    Document,
    DocumentCategory,
    DocumentChunk,
    DocumentVersion,
)


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for DocumentCategory entries."""

    list_display = (
        "code",
        "name",
        "level",
        "is_official",
        "minedu_reference",
    )
    list_filter = ("level", "is_official")
    search_fields = ("code", "name", "description", "minedu_reference")
    ordering = ("level", "name")
    prepopulated_fields = {"code": ("name",)}
    list_editable = ("is_official",)

    fieldsets = (
        (None, {"fields": ("code", "name", "description")}),
        (
            "Classification",
            {
                "fields": (
                    "level",
                    "is_official",
                    "minedu_reference",
                ),
            },
        ),
    )


class DocumentVersionInline(admin.TabularInline):
    """Inline table of versions inside Document admin."""

    model = DocumentVersion
    extra = 0

    fields = (
        "file",
        "status",
        "source",
        "created_by",
        "created_at",
        "page_count",
        "language",
        "is_indexed",
        "is_structured_ready",
        "structured_generated_at",
    )

    readonly_fields = (
        "created_at",
        "is_indexed",
        "is_structured_ready",
        "structured_generated_at",
    )

    ordering = ("-created_at",)
    show_change_link = True


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Documents."""

    list_display = (
        "title",
        "owner",
        "category",
        "school",
        "current_version",
        "is_archived",
        "is_current",
        "updated_at",
    )
    list_filter = (
        "category",
        "category__level",
        "school",
        "is_archived",
        "is_current",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "official_code",
        "official_number",
        "issuing_entity",
        "owner__email",
        "owner__first_name",
        "owner__last_name",
    )
    autocomplete_fields = ("owner", "school", "category", "current_version")
    ordering = ("-updated_at",)
    inlines = [DocumentVersionInline]
    list_select_related = ("owner", "category", "school", "current_version")

    fieldsets = (
        (
            "Document Info",
            {
                "fields": (
                    "title",
                    "description",
                    "category",
                    "school",
                    "owner",
                ),
            },
        ),
        (
            "Normative metadata",
            {
                "fields": (
                    "official_code",
                    "official_number",
                    "official_year",
                    "issuing_entity",
                    "official_url",
                    "valid_from",
                    "valid_until",
                    "is_current",
                ),
            },
        ),
        (
            "Versioning",
            {
                "fields": (
                    "current_version",
                    "is_archived",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")


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


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Admin configuration for document versions."""

    list_display = (
        "id",
        "document",
        "status",
        "source",
        "created_by",
        "created_at",
        "page_count",
        "language",
        "is_indexed",
        "is_structured_ready",
        "structured_generated_at",
    )
    list_filter = (
        "status",
        "source",
        "language",
        "is_indexed",
        "is_structured_ready",
        "created_at",
    )
    search_fields = (
        "document__title",
        "original_filename",
        "created_by__email",
    )
    autocomplete_fields = ("document", "created_by")
    ordering = ("-created_at",)
    inlines = [DocumentChunkInline]
    list_select_related = ("document", "created_by")

    fieldsets = (
        (
            "Base",
            {
                "fields": (
                    "document",
                    "file",
                    "status",
                    "source",
                    "created_by",
                ),
            },
        ),
        (
            "File metadata",
            {
                "fields": (
                    "original_filename",
                    "mime_type",
                    "checksum",
                    "page_count",
                    "language",
                ),
            },
        ),
        (
            "AI processing",
            {
                "fields": (
                    "ai_summary",
                    "is_indexed",
                    "indexing_error",
                ),
            },
        ),
        (
            "Structured content",
            {
                "fields": (
                    "is_structured_ready",
                    "structured_generated_at",
                    "structured_content",
                    "structured_error",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "is_indexed",
        "ai_summary",
        "is_structured_ready",
        "structured_generated_at",
        "structured_content",
    )


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
