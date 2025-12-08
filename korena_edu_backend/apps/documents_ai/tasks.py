import logging
from typing import Any, Dict, List

from django.utils import timezone

from celery import shared_task

from apps.core.metrics import track_celery_task
from apps.core.tasks import dispatch_after_commit
from apps.documents.models.documents import DocumentVersion
from apps.documents_ai.models.choices import DocumentChunkCategory
from apps.documents_ai.models.documents_ai import DocumentChunk
from apps.documents_ai.parsers.docx_parser import parse_docx_to_structured
from apps.documents_ai.parsers.pdf_parser import parse_pdf_to_structured
from apps.documents_ai.services.chunking import build_chunks_from_structured
from apps.documents_ai.services.embedding import get_embeddings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
@track_celery_task("process_document_version_for_structure")
def process_document_version_for_structure(self: Any, version_id: int) -> None:
    """Build structured_content JSON for a DocumentVersion and trigger chunking."""
    version: DocumentVersion | None = None

    try:
        version = DocumentVersion.objects.get(id=version_id)

        file_name = version.file.name or ""
        extension = ""
        if "." in file_name:
            extension = file_name.lower().rsplit(".", 1)[-1]

        if extension not in {"pdf", "docx"}:
            version.is_structured_ready = False
            version.structured_error = (
                f"Tipo de archivo no soportado para procesamiento estructurado: "
                f".{extension or 'desconocido'}."
            )
            version.structured_generated_at = None
            version.save(
                update_fields=[
                    "is_structured_ready",
                    "structured_error",
                    "structured_generated_at",
                ],
            )

            return

        file_path = version.file.path

        if extension == "pdf":
            structured_content: Dict[str, Any] = parse_pdf_to_structured(file_path)
        else:
            structured_content = parse_docx_to_structured(file_path)

        if not isinstance(structured_content, dict):
            structured_content = {}

        version.structured_content = structured_content
        version.structured_generated_at = timezone.now()
        version.is_structured_ready = True
        version.structured_error = ""

        version.save(
            update_fields=[
                "structured_content",
                "structured_generated_at",
                "is_structured_ready",
                "structured_error",
            ],
        )

        dispatch_after_commit(
            build_chunks_for_document_version.delay,
            version.id,
        )

        return

    except DocumentVersion.DoesNotExist:
        logger.exception(
            "Error processing structured content (DocumentVersion id=%s). DocumentVersion.DoesNotExist",
            version_id,
        )

        return

    except Exception as exc:
        if version is not None:
            version.is_structured_ready = False
            version.structured_error = str(exc)
            version.structured_generated_at = None
            version.save(
                update_fields=[
                    "is_structured_ready",
                    "structured_error",
                    "structured_generated_at",
                ],
            )

        logger.exception(
            "Error processing structured content (DocumentVersion id=%s).",
            version_id,
        )

        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3)
@track_celery_task("build_chunks_for_document_version")
def build_chunks_for_document_version(self: Any, version_id: int) -> None:
    """Create DocumentChunk rows from structured_content and trigger embeddings."""
    version: DocumentVersion | None = None

    try:
        version = DocumentVersion.objects.get(id=version_id)

        if not version.is_structured_ready or not version.structured_content:
            version.is_chunking_ready = False
            version.chunking_error = (
                "El contenido estructurado aún no está listo para generar fragmentos."
            )
            version.chunking_generated_at = None
            version.save(
                update_fields=[
                    "is_chunking_ready",
                    "chunking_error",
                    "chunking_generated_at",
                ],
            )

            return

        DocumentChunk.objects.filter(version=version).delete()

        raw_chunks: List[Dict[str, Any]] = build_chunks_from_structured(
            version.structured_content,
            start_index=0,
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

        version.is_chunking_ready = True
        version.chunking_error = ""
        version.chunking_generated_at = timezone.now()
        version.save(
            update_fields=[
                "is_chunking_ready",
                "chunking_error",
                "chunking_generated_at",
            ],
        )

        dispatch_after_commit(
            generate_embeddings_for_document_version.delay,
            version.id,
        )

        return

    except DocumentVersion.DoesNotExist:

        return

    except Exception as exc:
        if version is not None:
            version.is_chunking_ready = False
            version.chunking_error = str(exc)
            version.chunking_generated_at = None
            version.save(
                update_fields=[
                    "is_chunking_ready",
                    "chunking_error",
                    "chunking_generated_at",
                ],
            )

        logger.exception(
            "Error building chunks (DocumentVersion id=%s).",
            version_id,
        )

        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3)
@track_celery_task("generate_embeddings_for_document_version")
def generate_embeddings_for_document_version(self: Any, version_id: int) -> None:
    """Generate embeddings for all chunks of a version."""
    try:
        version = DocumentVersion.objects.get(id=version_id)
    except DocumentVersion.DoesNotExist:

        return

    try:
        chunks = list(
            DocumentChunk.objects.filter(
                version=version,
                embedding__isnull=True,
            ).order_by("index"),
        )

        if not chunks:
            version.is_embeddings_ready = True
            version.embeddings_error = ""
            version.embeddings_generated_at = timezone.now()
            version.save(
                update_fields=[
                    "is_embeddings_ready",
                    "embeddings_error",
                    "embeddings_generated_at",
                ],
            )

            return

        texts = [chunk.content for chunk in chunks]
        vectors = get_embeddings(texts)

        if len(vectors) != len(chunks):
            logger.warning(
                "Embedding count mismatch for version id=%s: %s chunks, %s vectors",
                version_id,
                len(chunks),
                len(vectors),
            )
            version.is_embeddings_ready = False
            version.embeddings_error = (
                "Desajuste entre cantidad de chunks y embeddings generados."
            )
            version.embeddings_generated_at = None
            version.save(
                update_fields=[
                    "is_embeddings_ready",
                    "embeddings_error",
                    "embeddings_generated_at",
                ],
            )

            return

        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector

        DocumentChunk.objects.bulk_update(
            chunks,
            ["embedding"],
        )

        version.is_embeddings_ready = True
        version.embeddings_error = ""
        version.embeddings_generated_at = timezone.now()
        version.save(
            update_fields=[
                "is_embeddings_ready",
                "embeddings_error",
                "embeddings_generated_at",
            ],
        )

        return

    except Exception as exc:
        logger.exception(
            "Error generating embeddings (DocumentVersion id=%s).",
            version_id,
        )
        version.is_embeddings_ready = False
        version.embeddings_error = str(exc)
        version.embeddings_generated_at = None
        version.save(
            update_fields=[
                "is_embeddings_ready",
                "embeddings_error",
                "embeddings_generated_at",
            ],
        )

        raise self.retry(exc=exc, countdown=5)
