import re
from typing import Any, Dict, List

Block = Dict[str, Any]


# =============================================================================
# REGEX PATTERNS (legal-focused)
# =============================================================================

# Generic article token: Art., Art, Artículo, Articulo + number.
ARTICLE_TOKEN_RE = re.compile(
    r"""
    (?P<label>                # 'Art', 'Art.', 'Articulo', 'Artículo'
        (?:art(?:[íi]culo)?\.?)
    )
    \s*
    (?P<num>\d+)
    \s*
    [°ºo]?
    \s*
    [\.\-]?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Article at the start of the string.
ARTICLE_AT_START_RE = re.compile(
    r"^\s*" + ARTICLE_TOKEN_RE.pattern,
    re.IGNORECASE | re.VERBOSE,
)

# TÍTULO / CAPÍTULO headings with roman numerals.
TITLE_RE = re.compile(r"^T[ÍI]TULO\s+[IVXLC]+", re.IGNORECASE)
CHAPTER_RE = re.compile(r"^CAP[ÍI]TULO\s+[IVXLC]+", re.IGNORECASE)

# TÍTULO or CAPÍTULO appearing inside a larger paragraph (for extraction).
INLINE_TITLE_RE = re.compile(r"T[ÍI]TULO\s+[IVXLC]+", re.IGNORECASE)
INLINE_CHAPTER_RE = re.compile(r"CAP[ÍI]TULO\s+[IVXLC]+", re.IGNORECASE)

# All-caps paragraphs promoted to headings.
UPPERCASE_RE = re.compile(r"^[A-ZÁÉÍÓÚÜÑ0-9\-\s]+$")

# Simple "a)" bullets at the beginning of the text.
LETTER_AT_START_RE = re.compile(r"^[a-z]\)")


# =============================================================================
# PUBLIC PIPELINE
# =============================================================================


def postprocess_blocks(blocks: List[Block]) -> List[Block]:
    """Full, legal-oriented post-processing pipeline for PDF/DOCX blocks.

    The goal is to obtain a clean, legal-friendly structure for RAG over
    laws, normas, directivas, etc.

    Steps:
        1) Normalize whitespace.
        2) Convert "> text" bullets to list_item.
        3) Promote uppercase paragraphs to headings.
        4) Extract inline TÍTULO / CAPÍTULO headings from big paragraphs.
        5) Split big headings "TÍTULO II UNIVERSALIZACIÓN..." in two.
        6) Promote "Artículo X..." paragraphs to headings.
        7) Split blocks that contain multiple "Artículo X..." segments.
        8) Split inline lists "a) ... b) ... c) ..." into list_item blocks.
        9) Normalize heading levels (Título, Capítulo, Artículo, others).
       10) Reindex block IDs to avoid duplicates.
    """
    blocks = _normalize_whitespace(blocks)
    blocks = _convert_bullets(blocks)
    blocks = _promote_uppercase_to_heading(blocks)
    blocks = _extract_inline_titles_and_chapters(blocks)
    blocks = _split_big_headings(blocks)
    blocks = _promote_articles_to_headings(blocks)
    blocks = _split_article_fusions(blocks)
    blocks = _split_inline_lettered_lists(blocks)
    blocks = _normalize_heading_levels(blocks)
    blocks = _reindex_blocks(blocks)

    return blocks


# =============================================================================
# STAGE 1 — NORMALIZATION
# =============================================================================


def _normalize_whitespace(blocks: List[Block]) -> List[Block]:
    """Normalize whitespace inside each block's text."""
    for block in blocks:
        text = block.get("text")
        if isinstance(text, str):
            block["text"] = re.sub(r"\s+", " ", text).strip()

    return blocks


# =============================================================================
# STAGE 2 — BULLETS
# =============================================================================


def _convert_bullets(blocks: List[Block]) -> List[Block]:
    """Convert '> text' style bullets into list_item blocks."""
    for block in blocks:
        text = block.get("text", "")
        if isinstance(text, str) and text.startswith(">"):
            block["type"] = "list_item"
            block["text"] = text.lstrip("> ").strip()

    return blocks


# =============================================================================
# STAGE 3 — UPPERCASE → HEADING
# =============================================================================


def _promote_uppercase_to_heading(blocks: List[Block]) -> List[Block]:
    """Promote all-uppercase paragraphs into heading level 2."""
    for block in blocks:
        if block.get("type") != "paragraph":
            continue

        text = block.get("text", "")
        if not isinstance(text, str):
            continue

        if len(text) > 4 and UPPERCASE_RE.match(text):
            block["type"] = "heading"
            block["level"] = 2

    return blocks


# =============================================================================
# STAGE 4 — INLINE TÍTULO / CAPÍTULO EXTRACTION
# =============================================================================


def _extract_inline_titles_and_chapters(blocks: List[Block]) -> List[Block]:
    """Extract 'TÍTULO X' or 'CAPÍTULO X' from inside large paragraphs.

    The rest of the paragraph is preserved. The user explicitly wants
    at least 'TÍTULO I' to appear as a separate heading, even if the
    surrounding text remains as a single paragraph.
    """
    new_blocks: List[Block] = []

    for block in blocks:
        block_type = block.get("type")
        text = block.get("text", "")
        if block_type != "paragraph" or not isinstance(text, str):
            new_blocks.append(block)
            continue

        title_match = INLINE_TITLE_RE.search(text)
        chapter_match = INLINE_CHAPTER_RE.search(text)

        # Prefer TÍTULO over CAPÍTULO if both appear.
        match = title_match or chapter_match
        if not match:
            new_blocks.append(block)
            continue

        before = text[: match.start()].strip()
        heading_text = match.group(0).strip()
        after = text[match.end() :].strip()

        if before:
            before_block = dict(block)
            before_block["text"] = before
            new_blocks.append(before_block)

        heading_block: Block = dict(block)
        heading_block["type"] = "heading"
        heading_block["text"] = heading_text
        # Level is normalized later.
        heading_block.pop("level", None)
        new_blocks.append(heading_block)

        if after:
            after_block = dict(block)
            after_block["text"] = after
            new_blocks.append(after_block)

    return new_blocks


# =============================================================================
# STAGE 5 — SPLIT BIG HEADINGS (TÍTULO / CAPÍTULO + subtitle)
# =============================================================================


def _split_big_headings(blocks: List[Block]) -> List[Block]:
    """Split 'TÍTULO II UNIVERSALIZACIÓN...' into two heading blocks.

    Works similarly for 'CAPÍTULO I DISPOSICIONES GENERALES'.
    """
    new_blocks: List[Block] = []

    pattern = re.compile(
        r"^(?P<head>(?:T[ÍI]TULO|CAP[ÍI]TULO)\s+[IVXLC]+)\s+(?P<rest>.+)$",
        re.IGNORECASE,
    )

    for block in blocks:
        if block.get("type") != "heading":
            new_blocks.append(block)
            continue

        text = block.get("text", "")
        if not isinstance(text, str):
            new_blocks.append(block)
            continue

        match = pattern.match(text)
        if not match:
            new_blocks.append(block)
            continue

        head_text = match.group("head").strip()
        rest_text = match.group("rest").strip()

        head_block: Block = dict(block)
        head_block["text"] = head_text
        new_blocks.append(head_block)

        subtitle_block: Block = dict(block)
        subtitle_block["text"] = rest_text
        # Subtitle level is normalized later.
        subtitle_block.pop("level", None)
        new_blocks.append(subtitle_block)

    return new_blocks


# =============================================================================
# STAGE 6 — PROMOTE ARTICLES
# =============================================================================


def _promote_articles_to_headings(blocks: List[Block]) -> List[Block]:
    """Promote paragraphs starting with 'Artículo X...' to headings."""
    for block in blocks:
        text = block.get("text", "")
        if block.get("type") not in ("paragraph", "heading"):
            continue
        if not isinstance(text, str):
            continue

        if ARTICLE_AT_START_RE.match(text):
            block["type"] = "heading"
            # Level is set later in _normalize_heading_levels.
            block.pop("level", None)

    return blocks


# =============================================================================
# STAGE 7 — SPLIT ARTICLE FUSIONS
# =============================================================================


def _split_article_fusions(blocks: List[Block]) -> List[Block]:
    """Split blocks that contain multiple 'Artículo X...' segments.

    Each resulting part is turned into an independent heading-like block.
    The body text remains attached to its article in the same block.
    """
    new_blocks: List[Block] = []

    for block in blocks:
        text = block.get("text", "")
        if block.get("type") not in ("paragraph", "heading"):
            new_blocks.append(block)
            continue
        if not isinstance(text, str):
            new_blocks.append(block)
            continue

        matches = list(ARTICLE_TOKEN_RE.finditer(text))
        if len(matches) <= 1:
            new_blocks.append(block)
            continue

        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            part = text[start:end].strip()
            if not part:
                continue

            new_block: Block = dict(block)
            new_block["text"] = part
            new_block["type"] = "heading"
            new_block.pop("level", None)
            new_blocks.append(new_block)

    return new_blocks


# =============================================================================
# STAGE 8 — SPLIT INLINE LETTERED LISTS
# =============================================================================


def _split_inline_lettered_lists(blocks: List[Block]) -> List[Block]:
    """Split paragraphs like 'a) ... b) ... c) ...' into list_item blocks."""
    new_blocks: List[Block] = []

    item_pattern = re.compile(r"\b([a-j])\)")

    for block in blocks:
        block_type = block.get("type")
        text = block.get("text", "")
        if block_type not in ("paragraph", "list_item") or not isinstance(text, str):
            new_blocks.append(block)
            continue

        # If it already starts with "a)" etc., just convert to list_item.
        if item_pattern.match(text) and LETTER_AT_START_RE.match(text):
            new_block = dict(block)
            new_block["type"] = "list_item"
            new_blocks.append(new_block)
            continue

        matches = list(item_pattern.finditer(text))
        if len(matches) <= 1:
            new_blocks.append(block)
            continue

        # Optional leading text before the first bullet (often a sentence
        # tipo "Son fines de la educación peruana:").
        leading = text[: matches[0].start()].strip()
        if leading:
            leading_block: Block = dict(block)
            leading_block["text"] = leading
            leading_block["type"] = block_type
            new_blocks.append(leading_block)

        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            part = text[start:end].strip()
            if not part:
                continue

            item_block: Block = dict(block)
            item_block["text"] = part
            item_block["type"] = "list_item"
            new_blocks.append(item_block)

    return new_blocks


# =============================================================================
# STAGE 9 — HEADING LEVEL NORMALIZATION
# =============================================================================


def _normalize_heading_levels(blocks: List[Block]) -> List[Block]:
    """Infer consistent heading levels for legal documents."""
    for block in blocks:
        if block.get("type") != "heading":
            continue

        text = block.get("text", "")
        if not isinstance(text, str):
            continue

        stripped = text.strip()

        if TITLE_RE.match(stripped):
            block["level"] = 1
            continue

        if CHAPTER_RE.match(stripped):
            block["level"] = 2
            continue

        if ARTICLE_AT_START_RE.match(stripped):
            block["level"] = 4
            continue

        if "level" not in block:
            block["level"] = 3

    return blocks


# =============================================================================
# STAGE 10 — REINDEX BLOCKS
# =============================================================================


def _reindex_blocks(blocks: List[Block]) -> List[Block]:
    """Regenerate block IDs sequentially to avoid duplicates."""
    for index, block in enumerate(blocks, start=1):
        block["id"] = f"b{index}"

    return blocks
