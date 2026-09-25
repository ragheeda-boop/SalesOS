import csv
import gzip

import pytest

from scripts import stage_master_contacts_v07 as stage


def write_accounts(path, rows):
    with gzip.open(path, "wt", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["Master Account ID", "Global_Company_ID"])
        writer.writeheader()
        writer.writerows(rows)


def write_contacts(path, rows):
    fields = [
        "global_person_id",
        "Linkage_Status",
        "matched_master_account_id",
        "Global_Company_ID",
        "email",
    ]
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def prepare_small_contract(monkeypatch, contact_count=3):
    monkeypatch.setattr(stage, "EXPECTED_ACCOUNT_ROWS", 2)
    monkeypatch.setattr(stage, "EXPECTED_CONTACT_ROWS", contact_count)
    monkeypatch.setattr(
        stage,
        "LINKAGE_COUNTS",
        {
            "RESOLVED_VIA_MA_TO_GCID_MAP": 1,
            "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW": 1,
            "NO_ACCOUNT_LINK": contact_count - 2,
        },
    )


def test_staging_preflight_accepts_exact_crosswalk_and_preserves_raw_cells(tmp_path, monkeypatch):
    accounts = tmp_path / "accounts.csv.gz"
    contacts = tmp_path / "contacts.csv"
    write_accounts(
        accounts,
        [
            {"Master Account ID": "MA-1", "Global_Company_ID": "GC-1"},
            {"Master Account ID": "MA-2", "Global_Company_ID": "GC-2"},
        ],
    )
    write_contacts(
        contacts,
        [
            {
                "global_person_id": "GP-1",
                "Linkage_Status": "RESOLVED_VIA_MA_TO_GCID_MAP",
                "matched_master_account_id": "MA-1",
                "Global_Company_ID": "GC-1",
                "email": "person@example.test",
            },
            {
                "global_person_id": "GP-2",
                "Linkage_Status": "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW",
                "matched_master_account_id": "MA-X",
                "Global_Company_ID": "",
                "email": "",
            },
            {
                "global_person_id": "GP-3",
                "Linkage_Status": "NO_ACCOUNT_LINK",
                "matched_master_account_id": "",
                "Global_Company_ID": "",
                "email": "",
            },
        ],
    )
    prepare_small_contract(monkeypatch)

    crosswalk = stage.load_company_crosswalk(accounts, stage.sha256_file(accounts))
    rows = stage.load_contacts(contacts, crosswalk, stage.sha256_file(contacts))

    assert crosswalk == {"MA-1": "GC-1", "MA-2": "GC-2"}
    assert rows[0]["email"] == "person@example.test"
    assert rows[1]["Global_Company_ID"] == ""


def test_staging_preflight_rejects_resolved_company_pair_mismatch(tmp_path, monkeypatch):
    contacts = tmp_path / "contacts.csv"
    write_contacts(
        contacts,
        [
            {
                "global_person_id": "GP-1",
                "Linkage_Status": "RESOLVED_VIA_MA_TO_GCID_MAP",
                "matched_master_account_id": "MA-1",
                "Global_Company_ID": "WRONG",
                "email": "person@example.test",
            },
            {
                "global_person_id": "GP-2",
                "Linkage_Status": "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW",
                "matched_master_account_id": "MA-X",
                "Global_Company_ID": "",
                "email": "",
            },
            {
                "global_person_id": "GP-3",
                "Linkage_Status": "NO_ACCOUNT_LINK",
                "matched_master_account_id": "",
                "Global_Company_ID": "",
                "email": "",
            },
        ],
    )
    prepare_small_contract(monkeypatch)

    with pytest.raises(ValueError, match="crosswalk"):
        stage.load_contacts(contacts, {"MA-1": "GC-1"}, stage.sha256_file(contacts))


def test_staging_preflight_rejects_duplicate_person_source_ids(tmp_path, monkeypatch):
    contacts = tmp_path / "contacts.csv"
    write_contacts(
        contacts,
        [
            {
                "global_person_id": "GP-1",
                "Linkage_Status": "RESOLVED_VIA_MA_TO_GCID_MAP",
                "matched_master_account_id": "MA-1",
                "Global_Company_ID": "GC-1",
                "email": "",
            },
            {
                "global_person_id": "GP-1",
                "Linkage_Status": "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW",
                "matched_master_account_id": "MA-X",
                "Global_Company_ID": "",
                "email": "",
            },
            {
                "global_person_id": "GP-3",
                "Linkage_Status": "NO_ACCOUNT_LINK",
                "matched_master_account_id": "",
                "Global_Company_ID": "",
                "email": "",
            },
        ],
    )
    prepare_small_contract(monkeypatch)

    with pytest.raises(ValueError, match="duplicate"):
        stage.load_contacts(contacts, {"MA-1": "GC-1"}, stage.sha256_file(contacts))
