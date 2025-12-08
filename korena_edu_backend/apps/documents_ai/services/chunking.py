from typing import Any, Dict, Iterable, List

from apps.documents_ai.models.documents_ai import DocumentChunkCategory


def build_chunks_from_structured(
    structured: Dict[str, Any],
    *,
    max_chars_per_chunk: int = 1200,
    start_index: int = 0,
) -> List[Dict[str, Any]]:
    """Build raw chunk specs from a structured_content dict.

    Args:
        structured: Dict with the shape:
            {
                "blocks": [
                    {
                        "id": "b1",
                        "type": "heading",
                        "level": 1,
                        "text": "...",
                        "page": 1,
                    },
                    {
                        "id": "b2",
                        "type": "paragraph",
                        "text": "...",
                        "page": 1,
                    },
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
        max_chars_per_chunk: Maximum characters per text slice.
        start_index: Initial index for chunks (useful for incremental chunking).

    Returns:
        List[Dict[str, Any]]: List of raw chunk dicts with keys:
            - "index"
            - "content"
            - "chunk_type"
            - "token_count"
            - "metadata"
    """
    structured = structured or {}
    blocks: List[Dict[str, Any]] = structured.get("blocks") or []

    segments: List[Dict[str, Any]] = []

    for block in blocks:
        b_type = (block.get("type") or "paragraph").lower()
        block_id = block.get("id")
        page = block.get("page")

        text: str = ""
        chunk_type: str = DocumentChunkCategory.PARAGRAPH

        if b_type == "heading":
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkCategory.HEADING

        elif b_type == "paragraph":
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkCategory.PARAGRAPH

        elif b_type == "list":
            # Represent list item as plain text; if you later need bullets
            # you can prefix with "- " or similar.
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkCategory.LIST

        elif b_type == "table":
            text = _table_to_markdown(
                columns=block.get("columns") or [],
                rows=block.get("rows") or [],
            )
            chunk_type = DocumentChunkCategory.TABLE

        else:
            # Fallback, just store whatever text we have.
            text = (block.get("text") or "").strip()
            chunk_type = DocumentChunkCategory.OTHER

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
            },
        )

    raw_chunks: List[Dict[str, Any]] = []
    next_index = start_index

    for segment in segments:
        text = segment["text"]
        chunk_type = segment["chunk_type"]
        base_metadata = segment["metadata"]

        for slice_index, slice_text in enumerate(
            _split_long_text(text, max_chars=max_chars_per_chunk),
        ):
            metadata = dict(base_metadata)
            metadata["slice_index"] = slice_index

            raw_chunks.append(
                {
                    "index": next_index,
                    "content": slice_text,
                    "chunk_type": chunk_type,
                    "token_count": _estimate_tokens(slice_text),
                    "metadata": metadata,
                },
            )
            next_index += 1

    return raw_chunks


# Helpers


def _split_long_text(text: str, *, max_chars: int) -> Iterable[str]:
    """Split long text into slices of at most `max_chars` characters.

    This is a simple, deterministic splitter; for most normative docs,
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
    """Render a simple table (columns + rows) to Markdown text.

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
        columns = [f"Col {i + 1}" for i in range(max_cols)]

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
