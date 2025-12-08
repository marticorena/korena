from typing import Any, Dict, List

from docx import Document as DocxDocument
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph


def parse_docx_to_structured(path: str) -> Dict[str, Any]:
    """Extract a minimal structured representation from a DOCX file.

    Returns a dict:
    {
        "blocks": [
            {"id": "b1", "type": "heading", "level": 1, "text": "...", "page": null},
            {"id": "b2", "type": "paragraph", "text": "...", "page": null},
            {
                "id": "b3",
                "type": "table",
                "columns": [...],
                "rows": [...],
                "page": null
            },
            ...
        ]
    }

    Note:
        DOCX does not expose page numbers easily, so `page` is set to None.
    """
    doc = DocxDocument(path)
    blocks: List[Dict[str, Any]] = []
    block_id = 1

    for item in _iter_block_items(doc):
        # Paragraph block
        if isinstance(item, DocxParagraph):
            text = item.text.strip()
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

            if _is_list_paragraph(style_name):
                blocks.append(
                    {
                        "id": f"b{block_id}",
                        "type": "list",
                        "text": text,
                        "page": None,
                    }
                )
                block_id += 1
                continue

            # Default: paragraph
            blocks.append(
                {
                    "id": f"b{block_id}",
                    "type": "paragraph",
                    "text": text,
                    "page": None,
                }
            )
            block_id += 1

        # Table block
        elif isinstance(item, DocxTable):
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

    return {"blocks": blocks}


# Helpers


def _iter_block_items(parent: Any):
    """Yield paragraphs and tables in document order.

    This walks the underlying XML so we preserve the actual order
    of paragraphs and tables as they appear in the document body.
    """
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


def _classify_heading(style_name: str) -> (bool, int):
    """Determine if a paragraph style looks like a heading.

    Returns:
        (is_heading, level)
    """
    if not style_name:
        return False, 0

    # Typical Word styles: "Heading 1", "Heading 2", etc.
    if "heading" in style_name:
        # Try to extract a level digit if present.
        for digit in range(1, 7):
            if str(digit) in style_name:
                return True, digit

        return True, 1

    return False, 0


def _is_list_paragraph(style_name: str) -> bool:
    """Determine if a paragraph style is likely a list item."""
    if not style_name:
        return False

    # Common patterns for list styles in Word documents.
    if "bullet" in style_name:
        return True
    if "list" in style_name:
        return True

    # "List Paragraph" is a very common style name.
    if style_name.strip() == "list paragraph":
        return True

    return False


def _parse_table(table: DocxTable) -> Dict[str, List[List[str]]]:
    """Convert a python-docx Table into a simple (columns, rows) structure."""
    rows: List[List[str]] = []

    for row in table.rows:
        row_cells: List[str] = []
        for cell in row.cells:
            cell_text = "\n".join(
                [p.text.strip() for p in cell.paragraphs if p.text.strip()]
            ).strip()
            row_cells.append(cell_text)
        rows.append(row_cells)

    if rows:
        first_row = rows[0]
        columns = [col if col else f"Col {i+1}" for i, col in enumerate(first_row)]
        data_rows = rows[1:]
    else:
        columns = []
        data_rows = []

    return {"columns": columns, "rows": data_rows}
