from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "school",
        "date_joined",
    )

    list_filter = (
        "role",
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

    autocomplete_fields = ("school",)

    fieldsets = (
        ("Basic Info", {"fields": ("email", "password")}),
        ("Personal Details", {"fields": ("first_name", "last_name")}),
        (
            "Account Status",
            {
                "fields": (
                    "role",
                    "is_active",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
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
