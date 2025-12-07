from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.documents.models.documents import DocumentVersion
from apps.documents.tasks import (
    process_document_version_for_structure,
)
from apps.documents_ai.tasks import (
    build_chunks_for_document_version,
    generate_embeddings_for_document_version,
)


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

    # Reset structured + indexing flags.
    instance.is_structured_ready = False
    instance.structured_generated_at = None
    instance.structured_content = {}
    instance.structured_error = ""
    instance.is_indexed = False
    instance.indexing_error = ""

    instance.save(
        update_fields=[
            "is_structured_ready",
            "structured_generated_at",
            "structured_content",
            "structured_error",
            "is_indexed",
            "indexing_error",
        ],
    )

    # 1) Build structured_content from the original file.
    process_document_version_for_structure.delay(instance.id)

    # 2) Once structure is ready, you *could* chain tasks instead of firing all at once,
    #    but for now we keep simple fire-and-forget; later you can use chords/chains.
    build_chunks_for_document_version.delay(instance.id)
    generate_embeddings_for_document_version.delay(instance.id)
