from django.contrib import admin

from apps.documents.models.documents import Document, DocumentCategory, DocumentVersion
from apps.documents_ai.admin import DocumentChunkInline


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
        "is_structured_ready",
        "structured_generated_at",
        "is_chunking_ready",
        "chunking_generated_at",
        "is_embeddings_ready",
        "embeddings_generated_at",
    )

    readonly_fields = (
        "created_at",
        "is_structured_ready",
        "structured_generated_at",
        "is_chunking_ready",
        "chunking_generated_at",
        "is_embeddings_ready",
        "embeddings_generated_at",
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
        "is_structured_ready",
        "is_chunking_ready",
        "is_embeddings_ready",
        "structured_generated_at",
        "chunking_generated_at",
        "embeddings_generated_at",
    )
    list_filter = (
        "status",
        "source",
        "is_structured_ready",
        "is_chunking_ready",
        "is_embeddings_ready",
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
            "AI processing",
            {
                "fields": (
                    "is_chunking_ready",
                    "chunking_generated_at",
                    "chunking_error",
                    "is_embeddings_ready",
                    "embeddings_generated_at",
                    "embeddings_error",
                    "ai_summary",
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
        "is_structured_ready",
        "structured_generated_at",
        "structured_content",
        "structured_error",
        "is_chunking_ready",
        "chunking_generated_at",
        "chunking_error",
        "is_embeddings_ready",
        "embeddings_generated_at",
        "embeddings_error",
        "ai_summary",
    )
