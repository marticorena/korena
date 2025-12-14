from django.contrib import admin

from apps.documents.models import Document, DocumentCategory, DocumentVersion


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for DocumentCategory entries."""

    list_display = (
        "code",
        "name",
        "level",
    )
    list_filter = ("level",)
    search_fields = (
        "code",
        "name",
        "description",
    )
    ordering = ("level", "name")
    prepopulated_fields = {"code": ("name",)}

    fieldsets = (
        (None, {"fields": ("code", "name", "description")}),
        ("Classification", {"fields": ("level",)}),
    )


class DocumentVersionInline(admin.TabularInline):
    """Inline table of versions inside Document admin."""

    model = DocumentVersion
    extra = 0

    fields = (
        "id",
        "file",
        "created_at",
    )
    readonly_fields = (
        "id",
        "created_at",
    )
    ordering = ("-created_at",)
    show_change_link = True


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Documents."""

    list_display = (
        "title",
        "owner",
        "school",
        "category",
        "current_version",
        "is_archived",
        "updated_at",
    )
    list_filter = (
        "category",
        "category__level",
        "is_archived",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "owner__email",
        "owner__first_name",
        "owner__last_name",
    )
    autocomplete_fields = (
        "owner",
        "school",
        "category",
        "current_version",
    )
    ordering = ("-updated_at",)
    inlines = [DocumentVersionInline]
    list_select_related = (
        "owner",
        "school",
        "category",
        "current_version",
    )

    fieldsets = (
        (
            "Document",
            {
                "fields": (
                    "title",
                    "description",
                    "category",
                    "owner",
                    "school",
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

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Admin configuration for document versions."""

    list_display = (
        "id",
        "document",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("document__title",)
    autocomplete_fields = ("document",)
    ordering = ("-created_at",)
    list_select_related = ("document",)

    fieldsets = (
        (
            "Base",
            {
                "fields": (
                    "document",
                    "file",
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
