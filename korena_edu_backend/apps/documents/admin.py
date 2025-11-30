from django.contrib import admin

from .models import (
    Document,
    DocumentType,
    DocumentVersion,
)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """Admin configuration for DocumentType entries."""

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
        ("Classification", {"fields": ("level", "is_official", "minedu_reference")}),
    )


class DocumentVersionInline(admin.TabularInline):
    """Inline table of versions shown inside the Document admin."""

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


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Documents."""

    list_display = (
        "title",
        "owner",
        "type",
        "school",
        "current_version",
        "is_archived",
        "updated_at",
    )
    list_filter = ("type", "school", "is_archived", "created_at")
    search_fields = (
        "title",
        "description",
        "owner__email",
        "owner__first_name",
        "owner__last_name",
    )
    autocomplete_fields = ("owner", "school", "type", "current_version")
    ordering = ("-updated_at",)

    inlines = [DocumentVersionInline]

    fieldsets = (
        (
            "Document Info",
            {
                "fields": ("title", "description", "type", "school", "owner"),
            },
        ),
        (
            "Versioning",
            {
                "fields": ("current_version", "is_archived"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
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
    list_filter = ("status", "source", "created_at")
    search_fields = ("document__title", "created_by__email")
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
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("ai_summary", "page_count", "created_at"),
            },
        ),
    )

    readonly_fields = ("created_at",)
