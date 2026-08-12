"""Wave-8 style: JSONFormatter must promote LogRecord extras for Railway.

Railway CLI/JSON often strips ``message``; evaluate / fan-out fields
(step, elapsed_ms, decision_id, …) must appear as top-level JSON keys.
"""

from __future__ import annotations

import json
import logging

from app.common.logging_config import JSONFormatter


def _format_with_extra(**extra) -> dict:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="decision_engine.evaluate",
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return json.loads(JSONFormatter().format(record))


def test_json_formatter_promotes_evaluate_fanout_fields():
    payload = _format_with_extra(
        step="scored",
        elapsed_ms=12.5,
        decision_id="did-1",
        event_type="decision.created",
        subscriber="il2a",
        retry=2,
        company_id="co-1",
        tenant_id="t-1",
    )
    assert payload["message"] == "decision_engine.evaluate"
    assert payload["step"] == "scored"
    assert payload["elapsed_ms"] == 12.5
    assert payload["decision_id"] == "did-1"
    assert payload["event_type"] == "decision.created"
    assert payload["subscriber"] == "il2a"
    assert payload["retry"] == 2
    assert payload["company_id"] == "co-1"
    assert payload["tenant_id"] == "t-1"


def test_json_formatter_keeps_zero_numeric_extras():
    payload = _format_with_extra(elapsed_ms=0, retry=0, tasks_created=0)
    assert payload["elapsed_ms"] == 0
    assert payload["retry"] == 0
    assert payload["tasks_created"] == 0


def test_json_formatter_omits_empty_string_extras():
    payload = _format_with_extra(decision_id="", step="enter")
    assert "decision_id" not in payload
    assert payload["step"] == "enter"
