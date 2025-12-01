from typing import Any, Dict, Iterable, List

from django.db import transaction

from apps.documents.models import (
    DocumentChunk,
    DocumentChunkType,
    DocumentVersion,
)


def build_chunks_from_structured(
    version: DocumentVersion,
    *,
    max_chars_per_chunk: int = 1200,
) -> List[DocumentChunk]:
    """Build DocumentChunk rows from a version's structured_content.

    This function assumes `version.structured_content` has the shape:
    {
        "blocks": [
            {"id": "b1", "type": "heading", "level": 1, "text": "...", "page": 1},
            {"id": "b2", "type": "paragraph", "text": "...", "page": 1},
            {
                "id": "t1",
                "type": "table",
                "columns": ["Col 1", "Col 2"],
                "rows": [["a", "b"], ["c", "d"]],
                "page": 2,
            },
            ...
        ]
    }

    For each block:
    - headings, paragraphs, lists → plain text chunks.
    - tables → markdown-formatted text chunks.
    - LONG texts are split into multiple chunks based on `max_chars_per_chunk`.

    Returns:
        List[DocumentChunk]: All chunks created for this version.
    """
    structured: Dict[str, Any] = version.structured_content or {}
    blocks: List[Dict[str, Any]] = structured.get("blocks") or []

    # Starting index (in case you want to re-chunk incrementally).
    next_index = version.chunks.count()

    segments: List[Dict[str, Any]] = []

    for block in blocks:
        b_type = (block.get("type") or "paragraph").lower()
        block_id = block.get("id")
        page = block.get("page")

        text: str = ""
        chunk_type: str = DocumentChunkType.PARAGRAPH

        if b_type == "heading":
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkType.HEADING

        elif b_type == "paragraph":
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkType.PARAGRAPH

        elif b_type == "list":
            # Represent list item as text; if you later need bullets you can
            # prefix with "- " or similar.
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkType.LIST

        elif b_type == "table":
            text = _table_to_markdown(
                columns=block.get("columns") or [],
                rows=block.get("rows") or [],
            )
            chunk_type = DocumentChunkType.TABLE

        else:
            # Fallback, just store whatever text we have.
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkType.OTHER

        if not text:
            continue

        base_metadata: Dict[str, Any] = {
            "block_id": block_id,
            "block_type": b_type,
            "page": page,
        }

        segments.append(
            {
                "text": text,
                "chunk_type": chunk_type,
                "metadata": base_metadata,
            }
        )

    created_chunks: List[DocumentChunk] = []

    with transaction.atomic():
        for segment in segments:
            text = segment["text"]
            chunk_type = segment["chunk_type"]
            base_metadata = segment["metadata"]

            for slice_index, slice_text in enumerate(
                _split_long_text(text, max_chars=max_chars_per_chunk)
            ):
                metadata = dict(base_metadata)
                metadata["slice_index"] = slice_index

                chunk = DocumentChunk.objects.create(
                    version=version,
                    index=next_index,
                    content=slice_text,
                    chunk_type=chunk_type,
                    token_count=_estimate_tokens(slice_text),
                    metadata=metadata,
                )
                created_chunks.append(chunk)
                next_index += 1

    return created_chunks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _split_long_text(text: str, *, max_chars: int) -> Iterable[str]:
    """Split long text into slices of at most `max_chars` characters.

    This is a simple, deterministic splitter; for most normative docs
    paragraphs/headings won't be huge, so this is mainly a safety net.
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    if len(cleaned) <= max_chars:
        return [cleaned]

    slices: List[str] = []
    start = 0
    length = len(cleaned)

    while start < length:
        end = min(start + max_chars, length)
        slices.append(cleaned[start:end].strip())
        start = end

    return slices


def _table_to_markdown(*, columns: List[str], rows: List[List[str]]) -> str:
    """Render a simple table (columns + rows) to markdown text.

    Example:
        columns = ["A", "B"]
        rows = [["1", "2"], ["3", "4"]]

    Produces:

        | A | B |
        | --- | --- |
        | 1 | 2 |
        | 3 | 4 |
    """
    if not columns and not rows:
        return ""

    # If no columns but we have rows, generate generic headers.
    if not columns and rows:
        max_cols = max(len(r) for r in rows)
        columns = [f"Col {i+1}" for i in range(max_cols)]

    # Normalize row lengths.
    normalized_rows: List[List[str]] = []
    for r in rows:
        row = list(r)
        if len(row) < len(columns):
            row += [""] * (len(columns) - len(row))
        elif len(row) > len(columns):
            row = row[: len(columns)]
        normalized_rows.append(row)

    header = "| " + " | ".join(_escape_md(c) for c in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"

    lines = [header, separator]
    for row in normalized_rows:
        line = "| " + " | ".join(_escape_md(c) for c in row) + " |"
        lines.append(line)

    return "\n".join(lines)


def _escape_md(text: str) -> str:
    """Very small markdown escape for '|' and backslash."""
    return (text or "").replace("\\", "\\\\").replace("|", "\\|").strip()


def _estimate_tokens(text: str) -> int:
    """Very rough token estimator based on whitespace splits."""
    stripped = text.strip()
    if not stripped:
        return 0

    # Super simple: one token per word.
    return len(stripped.split())
