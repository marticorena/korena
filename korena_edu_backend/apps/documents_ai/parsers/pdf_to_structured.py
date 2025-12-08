from typing import Any, Dict, List

import fitz  # PyMuPDF


def parse_pdf_to_structured(path: str) -> Dict[str, Any]:
    """Extract a minimal structured representation from a PDF file.

    Returns a dict:
    {
        "blocks": [
            {"id": "p1", "type": "paragraph", "text": "...", "page": 1},
            {"id": "h1", "type": "heading", "level": 1, "text": "...", "page": 2},
            {"id": "t1", "type": "table", "columns": [...], "rows": [...], "page": 3},
            ...
        ]
    }
    """
    doc = fitz.open(path)
    blocks: List[Dict[str, Any]] = []
    block_id = 1

    for page_index, page in enumerate(doc, start=1):
        textpage = page.get_text("dict")

        for b in textpage.get("blocks", []):
            # Skip blocks without lines
            if "lines" not in b:
                continue

            # Accumulate text inside the block
            text_parts: List[str] = []
            font_sizes: List[float] = []

            is_table_candidate = False
            row_cells: List[List[str]] = []

            for line in b["lines"]:
                line_text = ""
                cell_texts = []

                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if not span_text:
                        continue

                    # Collect text
                    line_text += span_text + " "

                    # For heading detection
                    size = span.get("size")
                    if isinstance(size, (int, float)):
                        font_sizes.append(size)

                    # Detect table-like patterns
                    if span_text and ("\t" in span_text or "  " in span_text):
                        is_table_candidate = True
                        cell_texts.append(span_text)

                if line_text.strip():
                    text_parts.append(line_text.strip())

                if cell_texts:
                    row_cells.append(cell_texts)

            # Empty block?
            if not text_parts:
                continue

            text_combined = " ".join(text_parts).strip()

            # --- Detect heading based on font size ---
            avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 10
            is_heading = avg_size >= 14  # Simple heuristic

            if is_heading:
                blocks.append(
                    {
                        "id": f"b{block_id}",
                        "type": "heading",
                        "level": 1,  # PDF doesn't give heading depth
                        "text": text_combined,
                        "page": page_index,
                    }
                )
                block_id += 1
                continue

            # --- Detect table ---
            if is_table_candidate and row_cells:
                parsed = _parse_table_rows(row_cells)
                blocks.append(
                    {
                        "id": f"b{block_id}",
                        "type": "table",
                        "columns": parsed["columns"],
                        "rows": parsed["rows"],
                        "page": page_index,
                    }
                )
                block_id += 1
                continue

            # --- Default: paragraph ---
            blocks.append(
                {
                    "id": f"b{block_id}",
                    "type": "paragraph",
                    "text": text_combined,
                    "page": page_index,
                }
            )
            block_id += 1

    return {"blocks": blocks}


def _parse_table_rows(raw_rows: List[List[str]]) -> Dict[str, Any]:
    """Convert raw row spans into a simple table structure."""
    rows: List[List[str]] = []
    for raw in raw_rows:
        cells = []
        for t in raw:
            if "\t" in t:
                cells.extend([c.strip() for c in t.split("\t")])
            else:
                parts = [c.strip() for c in t.split("  ") if c.strip()]
                cells.extend(parts)
        if cells:
            rows.append(cells)

    if rows:
        first = rows[0]
        cols = [f"Col {i+1}" for i in range(len(first))]
    else:
        cols = []

    return {"columns": cols, "rows": rows}
