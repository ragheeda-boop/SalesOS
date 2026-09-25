"""Dependency-free, reviewable PDF export for analytics reports."""

from __future__ import annotations

import json
from typing import Any


def render_report_pdf(rows: list[dict[str, Any]]) -> str:
    """Return a minimal valid PDF containing a compact JSON report preview."""
    payload = json.dumps(rows[:100], ensure_ascii=True, default=str)
    text = "SalesOS Analytics Report\\n" + payload[:3500]
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 8 Tf 36 760 Td ({text}) Tj ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream",
    ]
    output = "%PDF-1.4\n"
    offsets: list[int] = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output.encode("latin-1")))
        output += f"{index} 0 obj\n{obj}\nendobj\n"
    xref = len(output.encode("latin-1"))
    output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    output += "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    output += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    return output
