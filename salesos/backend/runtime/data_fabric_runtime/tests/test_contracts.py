"""Tests for Data Contracts."""

from __future__ import annotations

from datetime import date

import pytest

from runtime.data_fabric_runtime.contracts.balady import BaladyContract
from runtime.data_fabric_runtime.contracts.najiz import NajizContract
from runtime.data_fabric_runtime.contracts.ncnp import NcnpContract
from runtime.data_fabric_runtime.contracts.rega import RegaContract
from runtime.data_fabric_runtime.contracts.taqeem import TaqeemContract


class TestBaladyContract:
    def test_valid_contract(self):
        record = BaladyContract(
            cr_number="1234567890",
            name_ar="شركة الأمل",
            city="الرياض",
            status="active",
        )
        assert record.cr_number == "1234567890"
        assert record.name_ar == "شركة الأمل"

    def test_to_canonical(self):
        record = BaladyContract(
            cr_number="1234567890",
            name_ar="شركة الأمل",
            city="الرياض",
            status="active",
            incorporation_date=date(2020, 1, 15),
        )
        canonical = record.to_canonical()
        assert canonical["cr_number"] == "1234567890"
        assert canonical["incorporation_date"] == "2020-01-15"

    def test_cr_number_validation(self):
        with pytest.raises(ValueError, match="Invalid CR number"):
            BaladyContract(cr_number="123")


class TestTaqeemContract:
    def test_valid_contract(self):
        record = TaqeemContract(
            cr_number="1234567890",
            employees_count=50,
            capital=500000.0,
        )
        assert record.employees_count == 50
        assert record.capital == 500000.0

    def test_to_canonical(self):
        record = TaqeemContract(
            cr_number="1234567890",
            name_ar="شركة تقييم",
            city="جدة",
        )
        canonical = record.to_canonical()
        assert canonical["name_ar"] == "شركة تقييم"
        assert canonical["city"] == "جدة"


class TestNcnpContract:
    def test_valid_contract(self):
        record = NcnpContract(
            cr_number="1234567890",
            name_ar="شركة إشعار",
            employees_total=25,
        )
        assert record.employees_total == 25

    def test_to_canonical_renames_employees(self):
        record = NcnpContract(
            cr_number="1234567890",
            employees_total=30,
        )
        canonical = record.to_canonical()
        assert canonical["employees_count"] == 30


class TestNajizContract:
    def test_valid_contract(self):
        record = NajizContract(
            cr_number="1234567890",
            case_number="1445/1",
            case_type="تجاري",
            court="ديوان المظالم",
        )
        assert record.case_number == "1445/1"

    def test_to_canonical_prefixes_private_fields(self):
        record = NajizContract(
            cr_number="1234567890",
            case_number="1445/1",
            court="ديوان المظالم",
        )
        canonical = record.to_canonical()
        assert canonical["_case_number"] == "1445/1"
        assert canonical["_court"] == "ديوان المظالم"


class TestRegaContract:
    def test_valid_contract(self):
        record = RegaContract(
            cr_number="1234567890",
            name_ar="شركة عقارية",
            cr_type="وسيط عقاري",
            status="active",
        )
        assert record.cr_type == "وسيط عقاري"

    def test_to_canonical(self):
        record = RegaContract(
            cr_number="1234567890",
            name_ar="شركة عقارية",
        )
        canonical = record.to_canonical()
        assert canonical["name_ar"] == "شركة عقارية"
