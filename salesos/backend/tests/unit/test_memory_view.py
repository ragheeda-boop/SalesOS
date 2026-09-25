from datetime import UTC, datetime, timedelta

from domains.commercial.memory.view import MemoryViewItem, project_memory


def test_memory_view_preserves_provenance_and_hides_raw_payloads():
    now = datetime(2026, 9, 22, tzinfo=UTC)
    result = project_memory(
        [
            MemoryViewItem("m1", "c1", "Renewal discussed", "meeting", now, 1.2, "open"),
            MemoryViewItem("m0", "c1", "Initial call", "email", now - timedelta(days=1), -1, None),
        ]
    )
    assert [item["memory_id"] for item in result] == ["m1", "m0"]
    assert result[0]["confidence"] == 1.0
    assert "raw_payload" not in result[0]
