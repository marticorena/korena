from django.contrib import admin

from apps.documents.models.documents import Document, DocumentCategory, DocumentVersion


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for DocumentCategory entries."""

    list_display = (
        "code",
        "name",
        "level",
        "minedu_reference",
    )
    list_filter = ("level",)
    search_fields = ("code", "name", "description", "minedu_reference")
    ordering = ("level", "name")
    prepopulated_fields = {"code": ("name",)}

    fieldsets = (
        (None, {"fields": ("code", "name", "description")}),
        (
            "Classification",
            {
                "fields": (
                    "level",
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
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)
    show_change_link = True


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Documents."""

    list_display = (
        "title",
        "owner",
        "category",
        "current_version",
        "is_archived",
        "is_current",
        "updated_at",
    )
    list_filter = (
        "category",
        "category__level",
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
    autocomplete_fields = ("owner", "category", "current_version")
    ordering = ("-updated_at",)
    inlines = [DocumentVersionInline]
    list_select_related = ("owner", "category", "current_version")

    fieldsets = (
        (
            "Document Info",
            {
                "fields": (
                    "title",
                    "description",
                    "category",
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
    )
    list_filter = (
        "status",
        "source",
        "created_at",
    )
    search_fields = (
        "document__title",
        "original_filename",
        "created_by__email",
    )
    autocomplete_fields = ("document", "created_by")
    ordering = ("-created_at",)
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
            "Timestamps",
            {
                "fields": ("created_at",),
            },
        ),
    )

    readonly_fields = ("created_at",)
