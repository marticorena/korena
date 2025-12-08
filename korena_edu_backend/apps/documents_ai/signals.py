from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.tasks import dispatch_after_commit
from apps.documents.models.documents import DocumentVersion
from apps.documents_ai.tasks import process_document_version_for_structure


@receiver(post_save, sender=DocumentVersion)
def trigger_document_pipelines(
    sender: Any,
    instance: DocumentVersion,
    created: bool,
    **kwargs: Any,
) -> None:
    """Trigger background pipelines when a new DocumentVersion is created."""

    if not created:
        return

    instance.is_structured_ready = False
    instance.structured_generated_at = None
    instance.structured_content = {}
    instance.structured_error = ""

    instance.is_chunking_ready = False
    instance.chunking_generated_at = None
    instance.chunking_error = ""

    instance.is_embeddings_ready = False
    instance.embeddings_generated_at = None
    instance.embeddings_error = ""

    instance.save(
        update_fields=[
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
        ],
    )

    dispatch_after_commit(
        process_document_version_for_structure.delay,
        instance.id,
    )

    return
