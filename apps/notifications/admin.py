from django.contrib import admin

from apps.notifications.models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin configuration for EmailLog."""

    list_display = (
        "to_email",
        "subject",
        "status",
        "user",
        "created_at",
        "sent_at",
    )

    list_filter = (
        "status",
        "created_at",
        "sent_at",
    )

    search_fields = (
        "to_email",
        "from_email",
        "subject",
        "plain_message",
        "html_message",
        "error_message",
    )

    readonly_fields = (
        "created_at",
        "sent_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Information",
            {
                "fields": (
                    "from_email",
                    "to_email",
                    "user",
                    "subject",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "plain_message",
                    "html_message",
                )
            },
        ),
        (
            "Sent status",
            {
                "fields": (
                    "status",
                    "error_message",
                    "created_at",
                    "sent_at",
                )
            },
        ),
    )
