"""PO decision G3-2 (report 104): NCNP numbers are never CR anchors."""

from app.modules.master_data.phase6.classification import classify_corrected
from app.modules.master_data.phase6.pipeline import filter_cr_by_source

NCNP = frozenset({"NCNP"})


def test_ncnp_only_tokens_are_dropped():
    src = {"NCNP": {"cr": ["1000568900", "2230"], "domain": [], "phone": [], "name": []}}
    assert filter_cr_by_source(["1000568900", "2230"], src, NCNP) == []


def test_token_vouched_by_another_source_is_kept():
    src = {
        "NCNP": {"cr": ["1010123456"], "domain": [], "phone": [], "name": []},
        "SFDA": {"cr": ["1010123456"], "domain": [], "phone": [], "name": []},
    }
    assert filter_cr_by_source(["1010123456"], src, NCNP) == ["1010123456"]


def test_non_ncnp_tokens_untouched_and_rtl_marks_ignored():
    src = {
        "NCNP": {"cr": ["2230"], "domain": [], "phone": [], "name": []},
        "SFDA": {"cr": ["\u202d1010999999\u202c"], "domain": [], "phone": [], "name": []},
    }
    assert filter_cr_by_source(["1010999999", "2230"], src, NCNP) == ["1010999999"]


def test_rule_off_or_unattributed_account_is_unchanged():
    assert filter_cr_by_source(["2230"], {}, NCNP) == ["2230"]
    src = {"NCNP": {"cr": ["2230"], "domain": [], "phone": [], "name": []}}
    assert filter_cr_by_source(["2230"], src, frozenset()) == ["2230"]


def test_truncated_ncnp_number_no_longer_anchors_identity():
    before = classify_corrected(cr_number="1000568900", confidence="MATCHED")
    after = classify_corrected(cr_number=None, confidence="MATCHED")
    assert before.has_cr is True
    assert after.has_cr is False


def test_shared_domain_allowlist_loads_group_domains():
    from app.modules.master_data.phase6.pipeline import load_shared_domain_allowlist

    allow = load_shared_domain_allowlist()
    assert "nadec.com.sa" in allow
    assert "muqawil.org" not in allow and "gamil.com" not in allow


def test_entity_domain_excludes_shared_but_not_allowlisted():
    from app.modules.master_data.phase6.pipeline import Phase6Pipeline

    p = Phase6Pipeline(None, dry_run=True, shared_domain_threshold=5)
    p._shared_domains = {"muqawil.org"}
    assert p.version.endswith("+DOMSH5")
    assert not p._is_entity_domain("muqawil.org")
    assert p._is_entity_domain("nadec.com.sa")
    assert not p._is_entity_domain("gmail.com")


def test_dead_domains_are_not_entity_domains():
    from app.modules.master_data.phase6.pipeline import Phase6Pipeline, load_dead_domains

    dead = load_dead_domains()
    assert "sasintl.co" in dead and "nadec.com.sa" not in dead
    p = Phase6Pipeline(None, dry_run=True, exclude_dead_domains=True, require_domain_corroboration=True)
    assert p.version.endswith("+LIVE+CORR") and len(p.version) <= 32
    assert not p._is_entity_domain("sasintl.co")
    assert p._is_entity_domain("blominvest.sa")


def test_full_rule_set_version_fits_varchar32():
    from app.modules.master_data.phase6.pipeline import Phase6Pipeline

    p = Phase6Pipeline(None, dry_run=True, cr_excluded_sources=frozenset({"NCNP"}),
                       shared_domain_threshold=5, exclude_dead_domains=True,
                       require_domain_corroboration=True)
    assert p.version == "OPTION_C_1+NCNP+DS5+LV+CR"


def test_display_domain_rule_version_is_distinct_and_fits():
    from app.modules.master_data.phase6.pipeline import Phase6Pipeline

    p = Phase6Pipeline(None, dry_run=True, cr_excluded_sources=frozenset({"NCNP"}),
                       shared_domain_threshold=5, exclude_dead_domains=True,
                       require_domain_corroboration=True, display_domain_rule=True)
    assert p.version == "OPTION_C_1+NCNP+DS5+LV+CR+ED"
