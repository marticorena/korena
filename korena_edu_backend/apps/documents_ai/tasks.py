import logging
from typing import Any, Dict, List

from celery import shared_task

from apps.core.metrics import track_celery_task
from apps.documents.models.documents import DocumentVersion
from apps.documents_ai.models.choices import DocumentChunkCategory
from apps.documents_ai.models.documents_ai import DocumentChunk
from apps.documents_ai.utils.chunking import build_chunks_from_structured

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
@track_celery_task("generate_embeddings_for_document_version")
def generate_embeddings_for_document_version(self, version_id: int) -> None:
    """Generate embeddings for all chunks of a version.

    NOTE:
        This assumes you have some embedding backend (OpenAI, local model, etc.)
        exposed via a helper function.

        Expected helper signature (implement this yourself):

        >>> from apps.documents.utils.embeddings import get_embedding
        >>> def get_embedding(text: str) -> list[float]: ...

    The task:
    - Iterates chunks without embedding.
    - Calls get_embedding(content).
    - Persists embeddings in the VectorField.
    """
    from apps.documents.utils.embeddings import get_embedding  # local import

    try:
        version = DocumentVersion.objects.get(id=version_id)
    except DocumentVersion.DoesNotExist:
        return

    try:
        chunks = DocumentChunk.objects.filter(
            version=version,
            embedding__isnull=True,
        ).order_by("index")

        if not chunks.exists():
            return

        updated_chunks: list[DocumentChunk] = []

        for chunk in chunks:
            try:
                embedding = get_embedding(chunk.content)
                chunk.embedding = embedding
                updated_chunks.append(chunk)
            except Exception as embed_exc:
                logger.exception(
                    "Error generating embedding for chunk id=%s: %s",
                    chunk.id,
                    embed_exc,
                )
                # We do NOT fail the entire task for one bad chunk.

        if updated_chunks:
            DocumentChunk.objects.bulk_update(
                updated_chunks,
                ["embedding"],
            )

        return

    except Exception as exc:
        logger.exception(
            "Error generating embeddings (DocumentVersion id=%s).",
            version_id,
        )
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3)
@track_celery_task("build_chunks_for_document_version")
def build_chunks_for_document_version(self, version_id: int) -> None:
    """Create DocumentChunk rows from structured_content.

    This task:
    - Requires structured_content to be ready.
    - Deletes existing chunks for that version (idempotent).
    - Uses build_chunks_from_structured(...) to obtain chunk specs.
    - Bulk-creates DocumentChunk rows.
    - Marks is_indexed or stores indexing_error.
    """
    version: DocumentVersion | None = None

    try:
        version = DocumentVersion.objects.get(id=version_id)

        if not version.is_structured_ready or not version.structured_content:
            version.is_indexed = False
            version.indexing_error = (
                "El contenido estructurado aún no está listo para generar fragmentos."
            )
            version.save(
                update_fields=[
                    "is_indexed",
                    "indexing_error",
                ],
            )
            return

        # Remove previous chunks to keep the operation idempotent.
        DocumentChunk.objects.filter(version=version).delete()

        raw_chunks: List[Dict[str, Any]] = build_chunks_from_structured(
            version.structured_content
        )

        chunk_objects: List[DocumentChunk] = []

        for raw in raw_chunks:
            chunk_objects.append(
                DocumentChunk(
                    version=version,
                    index=raw.get("index", 0),
                    content=raw.get("content", ""),
                    chunk_type=raw.get("chunk_type", DocumentChunkCategory.PARAGRAPH),
                    token_count=raw.get("token_count"),
                    metadata=raw.get("metadata", {}),
                ),
            )

        if chunk_objects:
            DocumentChunk.objects.bulk_create(chunk_objects)

        version.is_indexed = True
        version.indexing_error = ""

        version.save(
            update_fields=[
                "is_indexed",
                "indexing_error",
            ],
        )

        return

    except DocumentVersion.DoesNotExist:
        return

    except Exception as exc:
        if version is not None:
            version.is_indexed = False
            version.indexing_error = str(exc)
            version.save(
                update_fields=[
                    "is_indexed",
                    "indexing_error",
                ],
            )

        logger.exception(
            "Error building chunks (DocumentVersion id=%s).",
            version_id,
        )

        raise self.retry(exc=exc, countdown=5)
