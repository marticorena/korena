from html import escape
from typing import Any, Dict, List

Block = Dict[str, Any]


def render_structured_content_to_html(blocks: List[Block]) -> str:
    """Render structured blocks into admin-safe HTML preview.

    This renderer wraps everything in a scoped container and applies a local
    CSS reset to prevent Django Admin global styles from affecting layout.

    Args:
        blocks: Structured content blocks.

    Returns:
        HTML string (includes a scoped <style>).
    """
    container_id = "korena-structured-preview"

    css = f"""
    <style>
      /* Scope everything to the preview container */
      #{container_id} {{
        max-width: 920px;
        padding: 16px 18px;
        border: 1px solid var(--hairline-color, rgba(255,255,255,.12));
        border-radius: 10px;
        background: rgba(255,255,255,.03);
      }}

      /* Local reset: avoid Django admin typography/layout bleeding in */
      #{container_id} :where(h1,h2,h3,h4,h5,h6,p,ul,ol,li,table,thead,tbody,tr,th,td,div,span) {{
        all: revert;
        box-sizing: border-box;
      }}

      /* Typography */
      #{container_id} {{
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
        line-height: 1.45;
      }}

      #{container_id} h1 {{
        font-size: 22px;
        margin: 0 0 12px 0;
        font-weight: 800;
      }}
      #{container_id} h2 {{
        font-size: 18px;
        margin: 18px 0 10px 0;
        font-weight: 750;
      }}
      #{container_id} h3 {{
        font-size: 16px;
        margin: 14px 0 8px 0;
        font-weight: 700;
      }}
      #{container_id} h4 {{
        font-size: 14px;
        margin: 12px 0 6px 0;
        font-weight: 700;
      }}
      #{container_id} p {{
        margin: 0 0 10px 0;
        font-size: 13px;
        opacity: .95;
      }}

      /* Lists */
      #{container_id} ul {{
        margin: 0 0 12px 0;
        padding-left: 18px;
      }}
      #{container_id} li {{
        margin: 0 0 6px 0;
        font-size: 13px;
      }}

      /* Tables */
      #{container_id} table {{
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0 14px 0;
        font-size: 12px;
      }}
      #{container_id} th,
      #{container_id} td {{
        border: 1px solid rgba(255,255,255,.12);
        padding: 6px 8px;
        vertical-align: top;
      }}
      #{container_id} th {{
        font-weight: 700;
        background: rgba(255,255,255,.06);
      }}

      /* Small separators between sections */
      #{container_id} .k-sep {{
        height: 1px;
        background: rgba(255,255,255,.10);
        margin: 14px 0;
      }}
    </style>
    """

    html: List[str] = [css, f"<div id='{container_id}'>"]
    open_list = False

    for block in blocks:
        block_type = block.get("type")
        text = escape(str(block.get("text", "")).strip())

        if not text and block_type != "table":
            continue

        if block_type == "heading":
            if open_list:
                html.append("</ul>")
                open_list = False

            level = block.get("level", 3)
            if not isinstance(level, int):
                level = 3
            level = min(max(level, 1), 6)

            html.append(f"<h{level}>{text}</h{level}>")

        elif block_type == "paragraph":
            if open_list:
                html.append("</ul>")
                open_list = False

            html.append(f"<p>{text}</p>")

        elif block_type == "list_item":
            if not open_list:
                html.append("<ul>")
                open_list = True

            html.append(f"<li>{text}</li>")

        elif block_type == "table":
            if open_list:
                html.append("</ul>")
                open_list = False

            columns = block.get("columns", [])
            rows = block.get("rows", [])

            html.append("<table>")
            if columns:
                html.append("<thead><tr>")
                for col in columns:
                    html.append(f"<th>{escape(str(col))}</th>")
                html.append("</tr></thead>")

            html.append("<tbody>")
            for row in rows:
                html.append("<tr>")
                if isinstance(row, list):
                    for cell in row:
                        html.append(f"<td>{escape(str(cell))}</td>")
                else:
                    html.append(f"<td>{escape(str(row))}</td>")
                html.append("</tr>")
            html.append("</tbody></table>")

    if open_list:
        html.append("</ul>")

    html.append("</div>")

    return "\n".join(html)
