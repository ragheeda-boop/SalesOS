"""Phase 7 sales-usability rules (PO decisions A2/A3, report 91)."""

from __future__ import annotations

from app.modules.master_data.phase7 import usability
from app.modules.master_data.phase7.usability import (
    CR_AMBIGUOUS_MULTI,
    GATES,
    NOT_READY,
    P1_REVIEW_OPEN,
    P2_STRATUM_NOT_ACCEPTED,
    P3_PAIR_PENDING,
    SHORT_CR_PENDING,
    Gate,
    account_blockers,
)


def _b(**kw):
    base = dict(sales_readiness="SALES_READY", review_priority="P1", cr_class="SAFE",
                in_pending_p3_pair=False, in_pending_short_cr=False)
    base.update(kw)
    return account_blockers(**base)


def _closed(*keys):
    return {k: (Gate(k, "CLOSED", "test") if k in keys else g) for k, g in GATES.items()}


def test_every_shipped_gate_is_open():
    assert all(g.status == "OPEN" for g in GATES.values())


def test_p1_ready_account_blocked_while_g4_open():
    assert _b() == [P1_REVIEW_OPEN]


def test_p2_account_blocked_until_its_own_stratum_is_accepted():
    kw = dict(sales_readiness="SALES_READY_WITH_REVIEW", review_priority="P2")
    assert _b(**kw) == [P2_STRATUM_NOT_ACCEPTED]
    # Accepting the other stratum does not unlock this one.
    assert _b(**kw, gates=_closed("G5:ENRICHMENT_REQUIRED")) == [P2_STRATUM_NOT_ACCEPTED]
    assert _b(**kw, gates=_closed("G5:SALES_READY_WITH_REVIEW")) == []


def test_pending_review_populations_block_even_when_priority_gates_close():
    gates = _closed("G4")
    assert _b(gates=gates) == []
    assert _b(in_pending_p3_pair=True, gates=gates) == [P3_PAIR_PENDING]
    assert _b(in_pending_short_cr=True, cr_class="SUSPICIOUS_MULTI", gates=gates) == [
        SHORT_CR_PENDING, CR_AMBIGUOUS_MULTI]


def test_not_ready_is_never_usable():
    assert NOT_READY in _b(sales_readiness="ENRICHMENT_REQUIRED",
                           gates=_closed(*GATES.keys()))


def test_unknown_gate_fails_closed():
    assert _b(gates={}) == [P1_REVIEW_OPEN]


def test_non_commercial_segment_blocks_even_when_every_gate_is_closed():
    # PO decision G5-3 (report 106): non-profits / government are a separate segment.
    closed = {k: usability.Gate(k, "CLOSED", "test") for k in usability.GATES}
    kwargs = dict(sales_readiness="SALES_READY", review_priority="P1", cr_class="SAFE",
                  in_pending_p3_pair=False, in_pending_short_cr=False, gates=closed)
    assert usability.account_blockers(**kwargs) == []
    assert usability.account_blockers(non_commercial=True, **kwargs) == [usability.NON_COMMERCIAL]


def test_out_of_market_only_for_apollo_only_foreign_city():
    assert usability.is_out_of_market(apollo_only=True, city="Pune") is True
    assert usability.is_out_of_market(apollo_only=True, city="Riyadh") is False
    assert usability.is_out_of_market(apollo_only=True, city="الرياض") is False
    assert usability.is_out_of_market(apollo_only=True, city="") is False
    assert usability.is_out_of_market(apollo_only=False, city="London") is False
    closed = {k: usability.Gate(k, "CLOSED", "test") for k in usability.GATES}
    assert usability.account_blockers(
        sales_readiness="SALES_READY", review_priority="P1", cr_class="SAFE",
        in_pending_p3_pair=False, in_pending_short_cr=False, out_of_market=True, gates=closed,
    ) == [usability.OUT_OF_MARKET]


def test_empty_city_falls_back_to_foreign_cctld():
    assert usability.is_out_of_market(apollo_only=True, city="", domain="rahulgroup.com.bd") is True
    assert usability.is_out_of_market(apollo_only=True, city="", domain="example.cn") is True
    assert usability.is_out_of_market(apollo_only=True, city="", domain="pine.sa") is False
    assert usability.is_out_of_market(apollo_only=True, city="", domain="excelunited.me") is False
    assert usability.is_out_of_market(apollo_only=True, city="", domain="bestebit.com") is False
    assert usability.is_out_of_market(apollo_only=False, city="", domain="x.com.bd") is False
