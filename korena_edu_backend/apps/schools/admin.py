from django.contrib import admin

from apps.schools.models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """Admin interface for the School model."""

    list_display = (
        "name",
        "code",
        "is_verified",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_verified",)
    search_fields = ("name", "code")
    ordering = ("name",)

    fieldsets = (
        ("School Information", {"fields": ("name", "code")}),
        ("Verification", {"fields": ("is_verified",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")
