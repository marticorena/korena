# apps/documents_ai/parsers/docx_parser.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from docx import Document as DocxDocument
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph

from apps.documents_ai.parsers.postprocess import postprocess_blocks

Block = Dict[str, Any]


def parse_docx_to_structured(path: str) -> Dict[str, Any]:
    """Extract a minimal structured representation from a DOCX file.

    Notes:
        - DOCX doesn't expose reliable page numbers, so "page" is None.
        - Lists are detected via numbering properties (numPr) and style/text fallbacks.

    Args:
        path: Absolute or relative path to the DOCX file.

    Returns:
        Dict[str, Any]: {"blocks": [...]} structure compatible with the PDF parser.
    """
    doc = DocxDocument(path)
    blocks: List[Block] = []
    block_id = 1

    for item in _iter_block_items(doc):
        if isinstance(item, DocxParagraph):
            text = (item.text or "").strip()
            if not text:
                continue

            style_name = _safe_style_name(item)
            is_heading, level = _classify_heading(style_name)

            if is_heading:
                blocks.append(
                    {
                        "id": f"b{block_id}",
                        "type": "heading",
                        "level": level,
                        "text": text,
                        "page": None,
                    }
                )
                block_id += 1
                continue

            if _is_list_paragraph(item, style_name):
                blocks.append(
                    {
                        "id": f"b{block_id}",
                        "type": "list_item",
                        "text": text,
                        "page": None,
                    }
                )
                block_id += 1
                continue

            blocks.append(
                {
                    "id": f"b{block_id}",
                    "type": "paragraph",
                    "text": text,
                    "page": None,
                }
            )
            block_id += 1
            continue

        if isinstance(item, DocxTable):
            table_struct = _parse_table(item)
            if table_struct["rows"]:
                blocks.append(
                    {
                        "id": f"b{block_id}",
                        "type": "table",
                        "columns": table_struct["columns"],
                        "rows": table_struct["rows"],
                        "page": None,
                    }
                )
                block_id += 1

    processed_blocks = postprocess_blocks(blocks)

    return {"blocks": processed_blocks}


def _iter_block_items(parent: Any) -> Iterable[Any]:
    """Yield paragraphs and tables in document order."""
    from docx.oxml.table import CT_Tbl  # type: ignore
    from docx.oxml.text.paragraph import CT_P  # type: ignore

    body = parent.element.body

    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield DocxParagraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield DocxTable(child, parent)


def _safe_style_name(paragraph: DocxParagraph) -> str:
    """Return the paragraph style name in lowercase, or empty string."""
    try:
        style = paragraph.style
        if style is None:
            return ""

        name = style.name or ""

        return str(name).lower()
    except Exception:
        return ""


def _classify_heading(style_name: str) -> Tuple[bool, int]:
    """Determine if a paragraph style looks like a heading.

    Args:
        style_name: Lowercase style name.

    Returns:
        Tuple[bool, int]: (is_heading, level).
    """
    if not style_name:
        return False, 0

    if "heading" in style_name or "título" in style_name or "titulo" in style_name:
        for digit in range(1, 10):
            if str(digit) in style_name:
                return True, digit

        return True, 1

    return False, 0


def _has_numbering(paragraph: DocxParagraph) -> bool:
    """Return True if the paragraph has numbering properties (numPr).

    This is the most reliable way to detect DOCX lists even when the style
    name is not "List Paragraph" or doesn't contain "bullet".
    """
    try:
        p = paragraph._p  # pylint: disable=protected-access
        p_pr = getattr(p, "pPr", None)
        if p_pr is None:
            return False

        num_pr = getattr(p_pr, "numPr", None)
        if num_pr is None:
            return False

        num_id = getattr(num_pr, "numId", None)
        ilvl = getattr(num_pr, "ilvl", None)

        return num_id is not None or ilvl is not None
    except Exception:
        return False


def _looks_like_bulleted_text(text: str) -> bool:
    """Fallback heuristic for bullet-like prefixes in plain text."""
    stripped = text.strip()
    if not stripped:
        return False

    bullet_prefixes = (
        "•",
        "·",
        "-",
        "–",
        "—",
        "▪",
        "▫",
        "○",
        "●",
        "🟥",
        "🟦",
        "🟩",
        "🟨",
        "🔹",
        "🔸",
        "👉",
        "➡️",
        "✔",
        "✅",
    )

    return stripped.startswith(bullet_prefixes)


def _is_list_paragraph(paragraph: DocxParagraph, style_name: str) -> bool:
    """Determine if a paragraph is likely a list item.

    Priority:
        1) numPr present (true DOCX list)
        2) style hints (bullet/list)
        3) text prefix fallback (•, -, emoji bullets)

    Args:
        paragraph: Docx paragraph object.
        style_name: Lowercase style name.

    Returns:
        bool: True if the paragraph should be treated as list_item.
    """
    if _has_numbering(paragraph):
        return True

    if style_name:
        if "bullet" in style_name:
            return True
        if "list" in style_name:
            return True
        if style_name.strip() == "list paragraph":
            return True

    text = (paragraph.text or "").strip()

    return _looks_like_bulleted_text(text)


def _parse_table(table: DocxTable) -> Dict[str, List[List[str]]]:
    """Convert a python-docx Table into a simple (columns, rows) structure.

    Args:
        table: python-docx table instance.

    Returns:
        Dict[str, List[List[str]]]: {"columns": [...], "rows": [...]}.
    """
    rows: List[List[str]] = []

    for row in table.rows:
        row_cells: List[str] = []
        for cell in row.cells:
            cell_text = "\n".join(
                [p.text.strip() for p in cell.paragraphs if (p.text or "").strip()]
            ).strip()
            row_cells.append(cell_text)
        rows.append(row_cells)

    if rows:
        first_row = rows[0]
        columns = [col if col else f"Col {i + 1}" for i, col in enumerate(first_row)]
        data_rows = rows[1:]
    else:
        columns = []
        data_rows = []

    return {"columns": columns, "rows": data_rows}
