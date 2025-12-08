from __future__ import annotations

import re
from typing import Any, Dict, List

Block = Dict[str, Any]


# =============================================================================
# PUBLIC ENTRYPOINT
# =============================================================================


def postprocess_blocks(blocks: List[Block]) -> List[Block]:
    """Full, generic post-processing pipeline for PDF/DOCX structured blocks.

    Steps:
        1) Normalize whitespace.
        2) Convert '> text' bullets to list_item.
        3) Split multi list-items (a) ... b) ...).
        4) Split giant headings (LEY / TITULO / CAPITULO / ARTICULO).
        5) Split mid-block CAPÍTULO + subtitle.
        6) Promote uppercase paragraphs to heading.
        7) Infer semantic types.
        8) Split article fusion (Artículo 14 ... Artículo 15).
        9) Merge article headings with titles.
       10) Normalize heading levels.
       11) Extract subtitles after TÍTULO / CAPÍTULO.
    """

    blocks = _normalize_whitespace(blocks)
    blocks = _convert_arrow_bullets(blocks)
    blocks = _split_multi_list_items(blocks)
    blocks = _split_big_headings(blocks)
    blocks = _split_mid_chapter_and_title(blocks)
    blocks = _promote_uppercase_paragraphs(blocks)
    blocks = _infer_semantic_types(blocks)
    blocks = _split_article_fusion(blocks)
    blocks = _merge_article_headings(blocks)
    blocks = _normalize_heading_levels(blocks)
    blocks = _extract_subtitles_after_titles(blocks)

    return blocks


# =============================================================================
# STEP 1 — Normalize whitespace
# =============================================================================


def _normalize_whitespace(blocks: List[Block]) -> List[Block]:
    for block in blocks:
        t = block.get("text")
        if isinstance(t, str):
            block["text"] = " ".join(t.split()).strip()
    return blocks


# =============================================================================
# STEP 2 — Convert "> En la Educación …" into list_item
# =============================================================================


def _convert_arrow_bullets(blocks: List[Block]) -> List[Block]:
    for block in blocks:
        text = block.get("text", "")
        if isinstance(text, str) and text.startswith("> "):
            block["type"] = "list_item"
            block["text"] = text[2:].strip()
    return blocks


# =============================================================================
# STEP 3 — Split multi list-items (a) ... b) ... c)…)
# =============================================================================

# aggressive split: lookahead for "a)" "b)" etc. anywhere
LIST_SPLIT_RE = re.compile(r"(?=[a-z]\))", re.IGNORECASE)


def _split_multi_list_items(blocks: List[Block]) -> List[Block]:
    new_blocks = []
    for block in blocks:
        if block.get("type") != "list_item":
            new_blocks.append(block)
            continue

        text = block["text"]
        parts = LIST_SPLIT_RE.split(text)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            new_blocks.append(block)
            continue

        for p in parts:
            nb = dict(block)
            nb["text"] = p
            new_blocks.append(nb)

    return new_blocks


# =============================================================================
# STEP 4 — Split giant headings (LEY / TITULO / CAPITULO / ARTICULO)
# =============================================================================

# tokens that define conceptual boundaries in Peruvian legal documents
TOKEN_CUTS = [
    r"\bLEY\b",
    r"\bLEY\s+N[Rº°]*\b",
    r"\bEL PRESIDENTE DE LA REPÚBLICA\b",
    r"\bPOR CUANTO\b",
    r"\bT[IÍ]TULO\s+[IVXLC]+\b",
    r"\bCAP[IÍ]TULO\s+[IVXLC]+\b",
    r"\bART[IÍ]CULO\s+\d+",
]

TOKEN_SPLIT = re.compile("(" + "|".join(TOKEN_CUTS) + ")", re.IGNORECASE)


def _split_big_headings(blocks: List[Block]) -> List[Block]:
    new_blocks = []

    for block in blocks:
        if block.get("type") != "heading":
            new_blocks.append(block)
            continue

        text = block["text"]
        if len(text) < 60:
            new_blocks.append(block)
            continue

        parts = TOKEN_SPLIT.split(text)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            new_blocks.append(block)
            continue

        # group token + optional following sentence
        rebuilt = []
        i = 0
        while i < len(parts):
            token = parts[i]
            nxt = parts[i + 1] if i + 1 < len(parts) else ""
            if nxt and not TOKEN_SPLIT.match(nxt):
                rebuilt.append(f"{token} {nxt}".strip())
                i += 2
            else:
                rebuilt.append(token)
                i += 1

        for txt in rebuilt:
            nb = dict(block)
            nb["text"] = txt
            new_blocks.append(nb)

    return new_blocks


# =============================================================================
# STEP 5 — Split “UNIVERSALIZACIÓN … CAPÍTULO I DISPOSICIONES GENERALES”
# =============================================================================

MID_CHAPTER_RE = re.compile(r"(.+?)\s+(CAP[IÍ]TULO\s+[IVXLC]+)\s+(.*)", re.IGNORECASE)


def _split_mid_chapter_and_title(blocks: List[Block]) -> List[Block]:
    new_blocks = []

    for block in blocks:
        if block.get("type") != "heading":
            new_blocks.append(block)
            continue

        text = block["text"]
        m = MID_CHAPTER_RE.match(text)
        if not m:
            new_blocks.append(block)
            continue

        before = m.group(1).strip()
        chapter = m.group(2).strip()
        subtitle = m.group(3).strip()

        # before → level of original
        nb1 = dict(block)
        nb1["text"] = before
        new_blocks.append(nb1)

        # chapter token
        nb2 = dict(block)
        nb2["text"] = chapter
        nb2["level"] = 3
        new_blocks.append(nb2)

        # subtitle
        nb3 = dict(block)
        nb3["text"] = subtitle
        nb3["level"] = 3
        new_blocks.append(nb3)

    return new_blocks


# =============================================================================
# STEP 6 — Promote uppercase short paragraphs to heading
# =============================================================================


def _promote_uppercase_paragraphs(blocks: List[Block]) -> List[Block]:
    for block in blocks:
        if block.get("type") != "paragraph":
            continue
        text = block.get("text", "")
        if text.isupper() and 2 <= len(text.split()) <= 10:
            block["type"] = "heading"
            block["level"] = 2
    return blocks


# =============================================================================
# STEP 7 — Semantic inference (paragraph → list_item / heading)
# =============================================================================


def _infer_semantic_types(blocks: List[Block]) -> List[Block]:
    for block in blocks:
        text = _safe_text(block)
        if not text:
            continue

        upper = text.upper()
        btype = block.get("type", "paragraph")

        # LIST ITEM
        if btype == "paragraph" and _looks_like_list_item(text):
            block["type"] = "list_item"
            continue

        # LAW TITLE
        if _looks_like_law_title(upper):
            block["type"] = "heading"
            block.setdefault("level", 1)
            continue

        # TITULO
        if _looks_like_title_heading(upper):
            block["type"] = "heading"
            block.setdefault("level", 2)
            continue

        # CAPITULO
        if _looks_like_chapter_heading(upper):
            block["type"] = "heading"
            block.setdefault("level", 3)
            continue

        # ARTICULO
        if _starts_with_articulo(text):
            block["type"] = "heading"
            block.setdefault("level", 4)
            continue

    return blocks


# =============================================================================
# STEP 8 — Split “Artículo 14 … Artículo 15” inside same block
# =============================================================================

ARTICLE_SPLIT = re.compile(r"(?=ART[IÍ]CULO\s+\d+)", re.IGNORECASE)


def _split_article_fusion(blocks: List[Block]) -> List[Block]:
    new_blocks = []
    for block in blocks:
        if block.get("type") != "heading":
            new_blocks.append(block)
            continue

        text = block["text"]
        parts = ARTICLE_SPLIT.split(text)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            new_blocks.append(block)
            continue

        for p in parts:
            nb = dict(block)
            nb["text"] = p
            new_blocks.append(nb)

    return new_blocks


# =============================================================================
# STEP 9 — Merge article headings with titles
# =============================================================================


def _merge_article_headings(blocks: List[Block]) -> List[Block]:
    merged = []
    i = 0
    n = len(blocks)

    while i < n:
        curr = blocks[i]
        curr_txt = _safe_text(curr)

        if curr.get("type") == "heading" and _starts_with_articulo(curr_txt):
            nxt = blocks[i + 1] if i + 1 < n else None
            nxt2 = blocks[i + 2] if i + 2 < n else None

            # ARTICLE NUMBER BLOCK
            if (
                nxt
                and nxt.get("type") == "heading"
                and _looks_like_article_number(_safe_text(nxt))
            ):
                combined = f"{curr_txt} {_safe_text(nxt)}"
                if (
                    nxt2
                    and nxt2.get("type") == "paragraph"
                    and _looks_like_short_title(_safe_text(nxt2))
                ):
                    combined += " " + _safe_text(nxt2)
                    nb = dict(curr)
                    nb["text"] = combined
                    merged.append(nb)
                    i += 3
                    continue

                nb = dict(curr)
                nb["text"] = combined
                merged.append(nb)
                i += 2
                continue

            merged.append(curr)
            i += 1
            continue

        merged.append(curr)
        i += 1

    return merged


# =============================================================================
# STEP 10 — Normalize heading levels
# =============================================================================


def _normalize_heading_levels(blocks: List[Block]) -> List[Block]:
    for block in blocks:
        if block.get("type") != "heading":
            continue

        text = _safe_text(block)
        upper = text.upper()

        if _looks_like_law_title(upper):
            block["level"] = 1
        elif _looks_like_title_heading(upper):
            block["level"] = 2
        elif _looks_like_chapter_heading(upper):
            block["level"] = 3
        elif _starts_with_articulo(text):
            block["level"] = 4
        else:
            block["level"] = block.get("level", 2)

    return blocks


# =============================================================================
# STEP 11 — Extract subtitles after titles/capitulos
# =============================================================================


def _extract_subtitles_after_titles(blocks: List[Block]) -> List[Block]:
    new = []
    i = 0
    n = len(blocks)

    while i < n:
        b = blocks[i]
        new.append(b)

        if b.get("type") == "heading" and b.get("level") in {2, 3}:
            if i + 1 < n:
                nxt = blocks[i + 1]
                txt = nxt.get("text", "")
                if (
                    nxt.get("type") == "paragraph"
                    and txt.isupper()
                    and 2 <= len(txt.split()) <= 12
                ):
                    promoted = dict(nxt)
                    promoted["type"] = "heading"
                    promoted["level"] = b["level"]
                    new.append(promoted)
                    i += 2
                    continue

        i += 1

    return new


# =============================================================================
# LOW LEVEL HELPERS
# =============================================================================


def _safe_text(block: Block) -> str:
    t = block.get("text")
    return t.strip() if isinstance(t, str) else ""


def _starts_with_articulo(text: str) -> bool:
    t = text.lower().strip()
    return t.startswith("artículo") or t.startswith("articulo")


def _looks_like_article_number(text: str) -> bool:
    t = text.strip()
    return bool(any(c.isdigit() for c in t) and any(c in ".-°º" for c in t))


def _looks_like_short_title(text: str) -> bool:
    t = text.strip()
    return bool(t and len(t) <= 120 and " " in t)


def _looks_like_law_title(upper: str) -> bool:
    return upper.startswith("LEY ")


def _looks_like_title_heading(upper: str) -> bool:
    return upper.startswith("TÍTULO ") or upper.startswith("TITULO ")


def _looks_like_chapter_heading(upper: str) -> bool:
    return upper.startswith("CAPÍTULO ") or upper.startswith("CAPITULO ")


def _looks_like_list_item(text: str) -> bool:
    t = text.lstrip()
    if not t:
        return False
    if len(t) >= 3 and t[0].isalpha() and t[1] in {")", "."} and t[2] == " ":
        return True
    if t[0] in {"•", "-", "–"}:
        return True
    return False
