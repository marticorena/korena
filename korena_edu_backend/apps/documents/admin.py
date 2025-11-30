from django.contrib import admin

from apps.documents.models import (
    Document,
    DocumentCategory,
    DocumentVersion,
)


# DOCUMENT CATEGORY ADMIN
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


# DOCUMENT VERSION INLINE (shown inside Document admin)
class DocumentVersionInline(admin.TabularInline):
    """Inline table of versions inside Document admin."""

    model = DocumentVersion
    extra = 0

    # Added HTML metadata fields
    fields = (
        "file",
        "status",
        "source",
        "created_by",
        "created_at",
        "page_count",
        "language",
        "is_indexed",
        "is_html_ready",
        "html_generated_at",
    )

    readonly_fields = (
        "created_at",
        "is_indexed",
        "is_html_ready",
        "html_generated_at",
    )

    ordering = ("-created_at",)


# DOCUMENT ADMIN
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


# DOCUMENT VERSION ADMIN
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
        "is_html_ready",  # NEW
        "html_generated_at",  # NEW
    )
    list_filter = (
        "status",
        "source",
        "language",
        "is_indexed",
        "is_html_ready",  # NEW
        "created_at",
    )
    search_fields = (
        "document__title",
        "original_filename",
        "created_by__email",
    )
    autocomplete_fields = ("document", "created_by")
    ordering = ("-created_at",)

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
                    "extracted_at",
                    "is_indexed",
                    "indexing_error",
                ),
            },
        ),
        (
            "HTML rendering",
            {
                "fields": (
                    "is_html_ready",
                    "html_generated_at",
                    "html_content",
                    "html_toc",
                    "html_error",
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

    # Fields turned readonly to avoid direct admin edits
    readonly_fields = (
        "created_at",
        "extracted_at",
        "is_indexed",
        "is_html_ready",
        "html_generated_at",
    )
