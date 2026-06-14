"""Tiny, safe markdown→HTML for briefing section bodies.

Handles only the subset the briefing produces: **bold**, `## ` headings,
`- ` bullet lists, and blank-line-separated paragraphs. HTML is escaped first,
so news titles / model output can't inject markup into the email.
"""

from __future__ import annotations

import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_BLANKLINE = re.compile(r"\n\s*\n")


def _inline(text: str) -> str:
    return _BOLD.sub(r"<strong>\1</strong>", html.escape(text))


def to_html(md: str, *, color: str = "#3a3a3a") -> str:
    blocks = _BLANKLINE.split(md.strip())
    out: list[str] = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        if all(ln.lstrip().startswith("- ") for ln in lines):
            items = "".join(f"<li style='margin:0 0 4px'>{_inline(ln.lstrip()[2:])}</li>" for ln in lines)
            out.append(f"<ul style='margin:0 0 14px;padding-left:18px;color:{color}'>{items}</ul>")
        elif block.startswith("## "):
            out.append(f"<h3 style='margin:18px 0 8px;font-size:15px;color:#111'>{_inline(block[3:])}</h3>")
        else:
            para = "<br>".join(_inline(ln) for ln in lines)
            out.append(f"<p style='margin:0 0 14px;line-height:1.6;color:{color}'>{para}</p>")
    return "\n".join(out)


def to_text(md: str) -> str:
    """Plain-text version: drop ** markers, keep bullets as-is."""
    return _BOLD.sub(r"\1", md).strip()
