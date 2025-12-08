from typing import Any, Dict, List

import fitz  # PyMuPDF

from apps.documents_ai.parsers.postprocess import postprocess_blocks

Block = Dict[str, Any]


def parse_pdf_to_structured(path: str) -> Dict[str, Any]:
    """Extract a minimal structured representation from a PDF file.

    The structure focuses on legal/educational documents and relies on a
    post-processing pipeline to infer headings, articles and list items.

    Returns:
        Dict[str, Any]: A dict with a single key "blocks", containing an
        ordered list of blocks:
            {
                "blocks": [
                    {"id": "b1", "type": "heading", "level": 1, "text": "...", "page": 1},
                    {"id": "b2", "type": "paragraph", "text": "...", "page": 1},
                    {"id": "b3", "type": "list_item", "text": "...", "page": 2},
                    ...
                ]
            }
    """
    doc = fitz.open(path)
    blocks: List[Block] = []
    block_id = 1

    for page_index, page in enumerate(doc, start=1):
        textpage = page.get_text("dict")

        for raw_block in textpage.get("blocks", []):
            if "lines" not in raw_block:
                continue

            text_parts: List[str] = []
            font_sizes: List[float] = []

            for line in raw_block["lines"]:
                line_text_parts: List[str] = []

                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if not isinstance(span_text, str):
                        continue

                    span_text = span_text.strip()
                    if not span_text:
                        continue

                    line_text_parts.append(span_text)

                    size = span.get("size")
                    if isinstance(size, (int, float)):
                        font_sizes.append(float(size))

                if line_text_parts:
                    line_text = " ".join(line_text_parts)
                    text_parts.append(line_text)

            if not text_parts:
                continue

            text_combined = " ".join(text_parts).strip()
            if not text_combined:
                continue

            avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 10.0
            is_heading = avg_size >= 14.0

            block: Block
            if is_heading:
                block = {
                    "id": f"b{block_id}",
                    "type": "heading",
                    "level": 1,
                    "text": text_combined,
                    "page": page_index,
                }
            else:
                block = {
                    "id": f"b{block_id}",
                    "type": "paragraph",
                    "text": text_combined,
                    "page": page_index,
                }

            blocks.append(block)
            block_id += 1

    processed_blocks = postprocess_blocks(blocks)

    return {"blocks": processed_blocks}
