from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    # Fields visible in the list page
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "school",
        "date_joined",
    )
    list_filter = (
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "school",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("email",)

    # Use autocomplete for foreign keys
    autocomplete_fields = ("school",)

    # What the admin uses as display labels
    fieldsets = (
        ("Basic Info", {"fields": ("email", "password")}),
        ("Personal Details", {"fields": ("first_name", "last_name")}),
        (
            "Role & Permissions",
            {
                "fields": (
                    "role",
                    "is_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("School Association", {"fields": ("school",)}),
        ("Important Dates", {"fields": ("date_joined", "last_login")}),
    )

    add_fieldsets = (
        (
            "Create User",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "role",
                    "is_verified",
                    "is_active",
                    "is_staff",
                    "school",
                ),
            },
        ),
    )

    readonly_fields = (
        "date_joined",
        "last_login",
    )
