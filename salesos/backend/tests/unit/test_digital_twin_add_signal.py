"""DigitalTwin.add_signal() was typed to accept `BuyingSignal`
(intelligence/signals/__init__.py -- fields: id/company_id/signal_type/
title/description/intensity/priority/source/detected_at/expires_at), but
appends directly into `business_object.signals`, which is declared
`list[ObjectSignal]` (intelligence/business_objects/__init__.py --
fields: id/type/title/description/source/source_url/confidence/
detected_at/expires_at). The two dataclasses are unrelated with
different field names (`signal_type`/`intensity`/`priority` vs
`type`/`confidence`/`source_url`) -- appending a real `BuyingSignal`
would silently put a wrongly-shaped object into a list every downstream
reader expects to hold `ObjectSignal` instances.

Confirmed dead code via repo-wide grep: `DigitalTwin.add_signal()` has
zero callers anywhere (Digital Twin is an ADR-103 explicitly-deferred
module) and zero prior test coverage. Fixed the parameter type to
`ObjectSignal`, matching the list it's actually appended to.
"""

from __future__ import annotations

from intelligence.business_objects import (
    BusinessObject,
    EntityType,
    ObjectIdentity,
    ObjectSignal,
    SignalType,
)
from intelligence.digital_twin.twin import DigitalTwin


def _make_twin() -> DigitalTwin:
    obj = BusinessObject(identity=ObjectIdentity(id="biz-1", entity_type=EntityType.COMPANY))
    return DigitalTwin(obj)


def test_add_signal_accepts_and_stores_a_real_object_signal():
    twin = _make_twin()
    signal = ObjectSignal(id="sig-1", type=SignalType.FUNDING, title="Series B raised")

    twin.add_signal(signal)

    assert len(twin.business_object.signals) == 1
    stored = twin.business_object.signals[0]
    assert isinstance(stored, ObjectSignal)
    assert stored.title == "Series B raised"
    assert twin.metrics.signal_count == 1
