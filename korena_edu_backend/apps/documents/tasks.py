import html as html_lib
import logging
import re
from typing import Dict, List, Tuple

from django.utils import timezone

from celery import shared_task
import fitz  # type: ignore[import]
import mammoth

from apps.core.metrics import track_celery_task
from apps.documents.models import DocumentVersion

logger = logging.getLogger(__name__)


def _render_pdf_to_html(path: str) -> Tuple[str, str, Dict[str, object]]:
    """Render a PDF file to simple HTML and plain text.

    The HTML is intentionally simple:
    - One <section> per page
    - Each page has an <h2> and a <pre> with escaped text
    The TOC is page-based (Página 1, Página 2, ...).

    Args:
        path: Absolute path to the PDF file on disk.

    Returns:
        Tuple[str, str, Dict[str, object]]: (html_content, extracted_text, toc).
    """

    document = fitz.open(path)
    body_parts: List[str] = []
    text_parts: List[str] = []
    toc_pages: List[Dict[str, object]] = []

    for page_index in range(len(document)):
        page = document[page_index]
        page_number = page_index + 1

        raw_text = page.get_text("text") or ""
        text_parts.append(raw_text.strip())

        anchor = f"page-{page_number}"
        toc_pages.append(
            {
                "label": f"Página {page_number}",
                "anchor": anchor,
                "page": page_number,
            },
        )

        safe_text = html_lib.escape(raw_text)
        section_html = (
            f'<section id="{anchor}">'
            f"<h2>Página {page_number}</h2>"
            f"<pre>{safe_text}</pre>"
            f"</section>"
        )
        body_parts.append(section_html)

    html_body = "\n".join(body_parts)
    full_html = f"<article>{html_body}</article>"
    extracted_text = "\n\n".join([part for part in text_parts if part])

    toc: Dict[str, object] = {
        "type": "pages",
        "items": toc_pages,
    }

    return full_html, extracted_text, toc


def _render_docx_to_html(path: str) -> Tuple[str, str, Dict[str, object]]:
    """Render a DOCX file to HTML and plain text using mammoth.

    Mammoth already produces clean, semantic HTML. This helper:
    - Converts DOCX → HTML.
    - Injects anchors for headings (h1–h6) to build a TOC.
    - Produces a basic TOC based on headings.
    - Derives a plain-text version by stripping tags.

    Args:
        path: Absolute path to the DOCX file on disk.

    Returns:
        Tuple[str, str, Dict[str, object]]: (html_content, extracted_text, toc).
    """

    with open(path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)

    html_content = result.value or ""

    # Build TOC based on headings (h1–h6).
    headings: List[Dict[str, object]] = []
    pattern = re.compile(
        r"<h([1-6])([^>]*)>(.*?)</h\1>",
        re.IGNORECASE | re.DOTALL,
    )

    # We will inject <span id="heading-{n}"></span> before each heading.
    def _strip_tags(text: str) -> str:
        """Remove HTML tags from a string."""

        cleaned = re.sub(r"<[^>]+>", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip()

    current_html = html_content
    new_html_parts: List[str] = []
    last_end = 0
    index_counter = 1

    for match in pattern.finditer(html_content):
        start, end = match.span()
        level_str = match.group(1)
        inner_html = match.group(3)

        level = int(level_str)
        title_text = _strip_tags(inner_html)
        anchor = f"heading-{index_counter}"

        # Append previous chunk.
        new_html_parts.append(current_html[last_end:start])

        heading_html = match.group(0)
        anchor_span = f'<span id="{anchor}"></span>'
        new_html_parts.append(anchor_span + heading_html)

        headings.append(
            {
                "label": title_text,
                "anchor": anchor,
                "level": level,
            },
        )

        last_end = end
        index_counter += 1

    new_html_parts.append(current_html[last_end:])
    final_html = "".join(new_html_parts) if headings else html_content

    # Extract plain text from final_html.
    text_no_tags = re.sub(r"<[^>]+>", " ", final_html)
    text_no_tags = re.sub(r"\s+", " ", text_no_tags).strip()

    toc: Dict[str, object] = {
        "type": "headings",
        "items": headings,
    }

    return final_html, text_no_tags, toc


@shared_task(bind=True, max_retries=3)
@track_celery_task("process_document_version_for_html")
def process_document_version_for_html(self, version_id: int) -> None:
    """Generate HTML representation for a DocumentVersion.

    Args:
        self: Celery task instance (used for retry logic).
        version_id (int): Primary key of the DocumentVersion to process.

    Raises:
        self.retry: Re-raised when an email fails, triggering a retry.

    This task:
    - Loads the version.
    - Detects extension (.pdf / .docx).
    - Delegates to the corresponding renderer.
    - Updates HTML, TOC, extracted_text and timestamps.
    - Marks is_html_ready or stores an error message in Spanish.
    """

    version: DocumentVersion | None = None

    try:
        version = DocumentVersion.objects.get(id=version_id)

        file_name = version.file.name or ""
        extension = ""
        if "." in file_name:
            extension = file_name.lower().rsplit(".", 1)[-1]

        # Only accept PDF and DOCX.
        if extension not in {"pdf", "docx"}:
            version.is_html_ready = False
            version.html_error = f"Tipo de archivo no soportado para vista HTML: .{extension or 'desconocido'}."
            version.save(
                update_fields=[
                    "is_html_ready",
                    "html_error",
                ],
            )

            return

        file_path = version.file.path

        if extension == "pdf":
            html_content, extracted_text, toc = _render_pdf_to_html(file_path)
        else:
            html_content, extracted_text, toc = _render_docx_to_html(file_path)

        version.html_content = html_content
        version.html_toc = toc
        if extracted_text:
            version.extracted_text = extracted_text
            version.extracted_at = timezone.now()
        version.is_html_ready = True
        version.html_error = ""
        version.html_generated_at = timezone.now()

        version.save(
            update_fields=[
                "html_content",
                "html_toc",
                "extracted_text",
                "extracted_at",
                "is_html_ready",
                "html_error",
                "html_generated_at",
            ],
        )

        return

    except DocumentVersion.DoesNotExist:
        # If the version does not exist anymore, we silently exit.
        return

    except Exception as exc:
        # Persist error on the version so it is visible from the admin/UI.
        if version is not None:
            version.is_html_ready = False
            version.html_error = str(exc)
            version.save(
                update_fields=[
                    "is_html_ready",
                    "html_error",
                ],
            )

        logger.exception(
            "Error processing document version (DocumentVersion id=%s).",
            version_id,
        )

        # Retry after 5 seconds
        raise self.retry(exc=exc, countdown=5)
