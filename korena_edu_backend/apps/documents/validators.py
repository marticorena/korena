from django.core.exceptions import ValidationError

from apps.core.messages import ERROR_MESSAGES


def validate_pdf_or_docx(file) -> None:
    """Validate that the uploaded file is PDF or DOCX."""

    name = (file.name or "").lower()

    if "." not in name:
        raise ValidationError(ERROR_MESSAGES["upload.invalid_document_format"])

    ext = name.rsplit(".", 1)[-1]

    if ext not in {"pdf", "docx"}:
        raise ValidationError(ERROR_MESSAGES["upload.invalid_document_format"])

    return
