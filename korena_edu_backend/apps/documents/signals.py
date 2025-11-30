from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.documents.models import DocumentVersion
from apps.documents.tasks import process_document_version_for_html


@receiver(post_save, sender=DocumentVersion)
def trigger_html_generation(
    sender: Any,
    instance: DocumentVersion,
    created: bool,
    **kwargs: Any,
) -> None:
    """Trigger HTML generation when a DocumentVersion is created.

    The actual conversion is delegated to a Celery task to avoid blocking
    the request/response cycle during file uploads.
    """

    if not created:

        return

    # Reset HTML-related fields before processing.
    instance.is_html_ready = False
    instance.html_error = ""
    instance.html_content = ""
    instance.html_toc = {}

    instance.save(
        update_fields=[
            "is_html_ready",
            "html_error",
            "html_content",
            "html_toc",
        ],
    )

    # Enqueue background task for HTML generation.
    process_document_version_for_html.delay(instance.id)

    return
