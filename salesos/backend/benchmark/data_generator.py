"""Generates realistic benchmark data: tenants, users, and companies.

Produces deterministic data (seeded random) for reproducible benchmarks.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

COMPANY_NAME_TEMPLATES_AR = [
    "شركة {name} للتجارة",
    "مؤسسة {name} للمقاولات",
    "شركة {name} القابضة",
    "مجموعة {name} التجارية",
    "شركة {name} للنقل",
    "مؤسسة {name} للخدمات",
    "شركة {name} العالمية",
    "شركة {name} العربية",
    "مصنع {name} للصناعة",
    "شركة {name} للتطوير",
    "مؤسسة {name} للعقارات",
    "شركة {name} للاستثمار",
    "شركة {name} التقنية",
    "مؤسسة {name} للمقاولات العامة",
    "شركة {name} المحدودة",
    "مؤسسة {name} للتجارة والمقاولات",
    "شركة {name} العقارية",
    "مستشفى {name} الطبي",
    "مكتب {name} للمحاماة",
    "شركة {name} للاتصالات",
]

NAME_PARTS = [
    "الأمل", "النور", "السلام", "البركة", "النجاح",
    "التميز", "الإبداع", "العلم", "القمة", "الريادة",
    "الجزيرة", "الخليج", "الواحة", "المدينة", "الدرة",
    "السهم", "القبلة", "المنار", "الينابيع", "الأصالة",
    "الحداثة", "الثقة", "الأمان", "الوفاء", "الإتقان",
    "الرقي", "الازدهار", "التقدم", "العمران", "الشروق",
    "الغد", "المستقبل", "الابتكار", "الارتقاء", "البناء",
]

CITIES = [
    "الرياض", "جدة", "مكة المكرمة", "المدينة المنورة", "الدمام",
    "الخبر", "الظهران", "تبوك", "بريدة", "حائل",
    "القصيم", "الطائف", "أبها", "خميس مشيط", "نجران",
    "جازان", "سكاكا", "عرعر", "الباحة", "ينبع",
]

REGIONS = [
    "الرياض", "مكة المكرمة", "المدينة المنورة", "الشرقية",
    "القصيم", "عسير", "تبوك", "حائل", "نجران",
    "جازان", "الحدود الشمالية", "الحدود الجنوبية", "الباحة", "الجوف",
]

STATUSES = ["active", "inactive", "suspended", "pending"]
ACTIVITIES = [
    "تجارة الجملة والتجزئة",
    "المقاولات العامة",
    "النقل والخدمات اللوجستية",
    "تقنية المعلومات",
    "العقارات والتطوير",
    "الصناعة والتصنيع",
    "الخدمات المالية",
    "الرعاية الصحية",
    "التعليم والتدريب",
    "الضيافة والسياحة",
    "الزراعة والثروة الحيوانية",
    "الاتصالات وتقنية المعلومات",
    "الخدمات الاستشارية",
    "المقاولات الكهربائية",
    "مقاولات الطرق والجسور",
]

LEGAL_FORMS = [
    "شركة ذات مسؤولية محدودة",
    "مؤسسة فردية",
    "شركة مساهمة مقفلة",
    "شركة مساهمة عامة",
    "شركة تضامن",
    "شركة توصية بسيطة",
]

CR_PREFIXES = ["10", "20", "30", "40", "50", "60", "70", "80", "90"]


class DataGenerator:

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def _pick(self, items: list[str]) -> str:
        return items[self._rng.randint(0, len(items) - 1)]

    def generate_tenant(self) -> dict[str, Any]:
        return {
            "id": uuid.UUID(int=self._rng.getrandbits(128)),
            "name": f"Tenant {self._rng.randint(1, 1000)}",
            "slug": f"tenant-{self._rng.randint(1, 1000)}",
            "is_active": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=self._rng.randint(1, 365)),
        }

    def generate_company(self, tenant_id: uuid.UUID, index: int) -> dict[str, Any]:
        name_part = self._pick(NAME_PARTS)
        name_ar = self._pick(COMPANY_NAME_TEMPLATES_AR).format(name=name_part)
        name_en = f"{name_part} Company {index}"

        city = self._pick(CITIES)
        region = self._pick(REGIONS)
        cr_prefix = self._pick(CR_PREFIXES)
        cr_number = f"{cr_prefix}{self._rng.randint(1000000, 9999999)}"

        created_at = datetime.now(timezone.utc) - timedelta(days=self._rng.randint(1, 730))
        updated_at = created_at + timedelta(days=self._rng.randint(0, 60))

        return {
            "id": uuid.UUID(int=self._rng.getrandbits(128)),
            "tenant_id": tenant_id,
            "name_ar": name_ar,
            "name_en": name_en,
            "cr_number": cr_number,
            "cr_type": self._rng.choice(["مؤسسة", "شركة"]),
            "status": self._pick(STATUSES),
            "city": city,
            "region": region,
            "phone": f"05{self._rng.randint(10000000, 99999999)}",
            "email": f"info@{name_en.lower().replace(' ', '')}.com.sa",
            "address": f"شارع {self._pick(CITIES)}، حي {self._pick(NAME_PARTS)}",
            "activity_description": self._pick(ACTIVITIES),
            "activity_code": f"{self._rng.randint(1000, 9999)}",
            "legal_form": self._pick(LEGAL_FORMS),
            "capital": self._rng.choice([100000, 500000, 1000000, 5000000, 10000000]),
            "employees_count": self._rng.choice([5, 10, 25, 50, 100, 200, 500]),
            "is_active": self._rng.random() > 0.1,
            "confidence_score": round(self._rng.random(), 2),
            "latitude": round(24.7136 + self._rng.uniform(-2, 2), 6),
            "longitude": round(46.6753 + self._rng.uniform(-2, 2), 6),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def generate_companies(self, tenant_id: uuid.UUID, count: int) -> list[dict[str, Any]]:
        return [self.generate_company(tenant_id, i) for i in range(count)]

    @staticmethod
    def _serialize(c: dict[str, Any]) -> dict[str, Any]:
        """Convert types for DB compatibility (UUID→str, UTC→naive)."""
        out = {}
        for k, v in c.items():
            if isinstance(v, uuid.UUID):
                out[k] = str(v)
            elif isinstance(v, datetime) and v.tzinfo is not None:
                out[k] = v.replace(tzinfo=None)  # naive UTC for TIMESTAMP
            else:
                out[k] = v
        return out

    @staticmethod
    def seed_database(db_session, companies: list[dict[str, Any]]) -> None:
        """Sync seed — for use with sync engines."""
        from sqlalchemy import text

        for c in companies:
            db_session.execute(
                text("""
                INSERT INTO companies (
                    id, tenant_id, name_ar, name_en, cr_number, cr_type,
                    status, city, region, phone, email, address,
                    activity_description, activity_code, legal_form,
                    capital, employees_count, is_active, confidence_score,
                    latitude, longitude, created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :name_ar, :name_en, :cr_number, :cr_type,
                    :status, :city, :region, :phone, :email, :address,
                    :activity_description, :activity_code, :legal_form,
                    :capital, :employees_count, :is_active, :confidence_score,
                    :latitude, :longitude, :created_at, :updated_at
                )
                """),
                DataGenerator._serialize(c),
            )
        db_session.commit()

    @staticmethod
    async def async_seed_database(db_session, companies: list[dict[str, Any]]) -> None:
        """Async seed — bulk insert for speed."""
        from sqlalchemy import text

        serialized = [DataGenerator._serialize(c) for c in companies]
        stmt = text("""
            INSERT INTO companies (
                id, tenant_id, name_ar, name_en, cr_number, cr_type,
                status, city, region, phone, email, address,
                activity_description, activity_code, legal_form,
                capital, employees_count, is_active, confidence_score,
                latitude, longitude, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :name_ar, :name_en, :cr_number, :cr_type,
                :status, :city, :region, :phone, :email, :address,
                :activity_description, :activity_code, :legal_form,
                :capital, :employees_count, :is_active, :confidence_score,
                :latitude, :longitude, :created_at, :updated_at
            )
        """)
        # Use executemany via conn.execute with list of params
        conn = await db_session.connection()
        await conn.execute(stmt, serialized)
        await db_session.commit()
