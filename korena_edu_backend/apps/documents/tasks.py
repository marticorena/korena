import logging
from typing import Any, Dict

from django.utils import timezone

from celery import shared_task

from apps.core.metrics import track_celery_task
from apps.documents.models.documents import DocumentVersion
from apps.documents.utils.docx_to_structured import parse_docx_to_structured
from apps.documents.utils.pdf_to_structured import parse_pdf_to_structured

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
@track_celery_task("process_document_version_for_structure")
def process_document_version_for_structure(self, version_id: int) -> None:
    """Build structured_content JSON for a DocumentVersion.

    This task:
    - Loads the version.
    - Detects extension (.pdf / .docx).
    - Delegates parsing to the corresponding structured parser.
    - Updates structured_content, timestamps and flags.
    - Sets is_structured_ready or stores a Spanish error message.
    """
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
            version.save(
                update_fields=[
                    "is_structured_ready",
                    "structured_error",
                ],
            )
            return

        file_path = version.file.path

        if extension == "pdf":
            structured_content: Dict[str, Any] = parse_pdf_to_structured(file_path)
        else:
            structured_content = parse_docx_to_structured(file_path)

        # Defensive default
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

        return

    except DocumentVersion.DoesNotExist:
        # If the version does not exist anymore, we silently exit.
        return

    except Exception as exc:
        if version is not None:
            version.is_structured_ready = False
            version.structured_error = str(exc)
            version.save(
                update_fields=[
                    "is_structured_ready",
                    "structured_error",
                ],
            )

        logger.exception(
            "Error processing structured content (DocumentVersion id=%s).",
            version_id,
        )

        # Retry after 5 seconds
        raise self.retry(exc=exc, countdown=5)
