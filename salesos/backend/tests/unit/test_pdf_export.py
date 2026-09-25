from domains.analytics.pdf_export import render_report_pdf


def test_pdf_export_returns_a_valid_pdf_header_and_xref():
    output = render_report_pdf([{"stage": "won", "value": 10}])
    assert output.startswith("%PDF-1.4")
    assert "xref" in output
    assert output.endswith("%%EOF\n")
