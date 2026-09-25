from app.modules.employee_360.buying_committee import (
    build_buying_committee,
    classify_committee_role,
)


def test_role_classification_is_explicit_and_evidence_backed():
    assert classify_committee_role("Chief Technology Officer") == ("technical_buyer", 0.85)
    role, confidence = classify_committee_role("Procurement Manager")
    assert role == "procurement"
    assert confidence == 0.85


def test_committee_is_sorted_and_does_not_mutate_source_rows():
    people = [
        {"id": "2", "name": "Unknown", "title": ""},
        {"id": "1", "name": "CFO", "title": "CFO"},
        {"id": "3", "name": "Buyer", "position": "Procurement Lead"},
        {"id": "missing-name", "name": "", "title": "CEO"},
    ]
    result = build_buying_committee(people)
    assert [member.person_id for member in result] == ["1", "3", "2"]
    assert result[0].role == "economic_buyer"
    assert result[1].role == "procurement"
    assert result[2].evidence == "title_missing_or_unclassified"
    assert people[0]["title"] == ""
