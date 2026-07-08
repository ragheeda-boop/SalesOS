"""SalesOS Demo Dataset Generator.

Generates bilingual (Arabic/English) demo data matching the actual DB schema:
- 1000+ companies, 5000+ contacts, 3000+ deals, 10000+ activities, 100+ users
- 10 sectors (مقاولات, صحة, تصنيع, تقنية, عقارات, طاقة, لوجستيك, غذاء, تجارة, اتصالات)
- Saudi cities, realistic names
- Licenses, timeline entries, golden_records
- Fully re-generatable (idempotent)

Usage:
    docker cp demo/seed_data.py muhide-api-1:/app/demo/
    docker exec muhide-api-1 python -m demo.seed_data --clear
    docker exec muhide-api-1 python -m demo.seed_data
"""

import argparse
import asyncio
import json
import random
import uuid as uuid_mod
from datetime import datetime, timedelta, timezone

SECTORS = [
    ("مقاولات", "Construction", ["مكتب هندسي", "مقاول عام", "مقاول كهرباء", "مقاول سباكة"]),
    ("صحة", "Healthcare", ["مستشفى", "مركز طبي", "عيادة", "مختبر"]),
    ("تصنيع", "Manufacturing", ["مصنع", "منتج", "ورشة صناعية"]),
    ("تقنية", "Technology", ["برمجيات", "حلول تقنية", "استضافة", "تطوير تطبيقات"]),
    ("عقارات", "Real Estate", ["تطوير عقاري", "وساطة عقارية", "إدارة أملاك"]),
    ("طاقة", "Energy", ["نفط وغاز", "طاقة متجددة", "بتروكيماويات"]),
    ("لوجستيك", "Logistics", ["نقل", "شحن", "تخزين", "توزيع"]),
    ("غذاء", "Food & Beverage", ["مطعم", "منتج غذائي", "مشروبات"]),
    ("تجارة", "Retail & Trade", ["تجزئة", "جملة", "استيراد وتصدير"]),
    ("اتصالات", "Telecom", ["اتصالات", "بنية تحتية", "خدمات رقمية"]),
]

CITIES = [
    ("الرياض", "Riyadh"), ("جدة", "Jeddah"), ("الدمام", "Dammam"),
    ("مكة", "Makkah"), ("المدينة", "Madinah"), ("الخبر", "Al Khobar"),
    ("الظهران", "Dhahran"), ("ينبع", "Yanbu"), ("تبوك", "Tabuk"),
    ("أبها", "Abha"), ("حائل", "Hail"), ("القصيم", "Qassim"),
    ("الجبيل", "Jubail"), ("القطيف", "Qatif"), ("الأحساء", "Ahsa"),
]

FIRST_NAMES_AR = [
    "محمد", "أحمد", "علي", "عمر", "خالد", "عبدالله", "فيصل", "سعود",
    "فهد", "ناصر", "سلمان", "بدر", "تركي", "ماجد", "حسن", "حسين",
    "إبراهيم", "يوسف", "سعد", "مشعل", "عزام", "نايف", "سلطان", "بندر",
]

FIRST_NAMES_AR_F = [
    "نورة", "سارة", "فاطمة", "مريم", "هدى", "أمل", "رنا", "لمى",
    "دلال", "منى", "هيفاء", "عزة", "ليلى", "رؤى", "حصة", "الجوهرة",
]

LAST_NAMES_AR = [
    "آل سعود", "القحطاني", "العتيبي", "الغامدي", "المطيري", "الدوسري",
    "الزهراني", "الشمري", "العنزي", "الحربي", "الجهني", "البلوي",
    "الشهري", "الثقفي", "المالكي", "البقمي", "السبيعي", "الرشيدي",
]

COMPANY_PREFIXES = ["شركة", "مؤسسة", "مجموعة", "مكتب"]

COMPANY_NAMES_AR = [
    "الجزيرة", "الوادي", "النخيل", "الساحل", "القمة", "الهدف",
    "البرج", "السهم", "النور", "الأفق", "البيان", "الصفوة",
    "الخليج", "الربيع", "الإتقان", "الريادة", "التقدم", "الإبداع",
]

POSITIONS = [
    ("الرئيس التنفيذي", "CEO"), ("المدير المالي", "CFO"),
    ("المدير التقني", "CTO"), ("مدير المبيعات", "Sales Director"),
    ("مدير التسويق", "Marketing Director"), ("مدير العمليات", "COO"),
    ("نائب الرئيس", "VP"), ("مدير مشاريع", "Project Manager"),
    ("رئيس قسم", "Department Head"),
    ("مدير تطوير الأعمال", "Business Development Manager"),
]

DEAL_STAGES = [
    ("تأهيل", "Qualification"), ("تحليل", "Analysis"),
    ("عرض", "Proposal"), ("تفاوض", "Negotiation"), ("إغلاق", "Closing"),
]

LICENSE_TYPES = ["بلدي", "تجاري", "صناعي", "مهني", "مقاولات"]
LICENSE_TYPE_EN = ["Municipal", "Commercial", "Industrial", "Professional", "Contracting"]


def rdate(start_year=2020, end_year=2025):
    s = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    e = datetime(end_year, 12, 31, tzinfo=timezone.utc)
    return s + timedelta(seconds=random.randint(0, int((e - s).total_seconds())))


def pick(items):
    return random.choice(items)


async def seed_database(counts: dict):
    import asyncpg

    dsn = "postgresql://salesos:salesos_dev_password@postgres:5432/salesos"
    conn = await asyncpg.connect(dsn)

    TID = "d1e2f3a4-5678-90ab-cdef-1234567890ab"
    TID_UUID = uuid_mod.UUID(TID)

    n_users = n_companies_actual = n_contacts = n_deals = n_activities = 0

    try:
        # Create tenant
        existing = await conn.fetchval("SELECT COUNT(*) FROM tenants WHERE id = $1", TID_UUID)
        if existing == 0:
            await conn.execute(
                "INSERT INTO tenants (id, name, slug, plan, is_active, created_at) VALUES ($1,$2,$3,$4,true,NOW())",
                TID_UUID, "Demo Tenant", "demo", "enterprise",
            )
            print("Created demo tenant")

        # Create users
        n_users = counts.get("users", 100)
        user_ids = []
        for i in range(n_users):
            uid = uuid_mod.uuid4()
            user_ids.append(uid)
            email = f"user{i+1}@salesos.demo"
            existing_u = await conn.fetchval("SELECT COUNT(*) FROM users WHERE email = $1", email)
            if existing_u == 0:
                await conn.execute(
                    """INSERT INTO users (id, tenant_id, email, password_hash, full_name, role, is_active, created_at)
                       VALUES ($1,$2,$3,$4,$5,$6,true,NOW())""",
                    uid, TID_UUID, email, "$2b$12$demo_password_hash", f"User {i+1}", pick(["admin", "manager", "user"]),
                )
        print(f"Created {n_users} users")

        # Create companies
        n_companies = counts.get("companies", 1000)
        company_ids = []
        for i in range(n_companies):
            sector_ar, sector_en, subs = pick(SECTORS)
            city_ar, city_en = pick(CITIES)
            prefix = pick(COMPANY_PREFIXES)
            name_ar = pick(COMPANY_NAMES_AR)
            status = pick(["active", "active", "active", "inactive"])
            industry = sector_ar
            cr = f"{random.randint(1000000000, 9999999999)}"

            existing_c = await conn.fetchval("SELECT COUNT(*) FROM companies WHERE cr_number = $1", cr)
            if existing_c > 0:
                continue

            cid = uuid_mod.uuid4()
            company_ids.append(cid)
            capital = random.choice([500000, 1000000, 5000000, 10000000, 50000000, 100000000])
            created = rdate(2020, 2023)

            await conn.execute(
                """INSERT INTO companies
                   (id, tenant_id, name_ar, name_en, cr_number, status, city, region,
                    industry, phone, email, website, capital, currency, employees_count,
                    is_active, is_golden_record, legal_form, incorporation_date, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,
                           true, false, $16, $17, $18)""",
                cid, TID_UUID,
                f"{prefix} {name_ar} {sector_ar}",
                f"{name_ar} {sector_en} Co.",
                cr, status, city_ar,
                "المنطقة الوسطى" if city_ar in ("الرياض", "القصيم") else "المنطقة الغربية" if city_ar in ("جدة", "مكة", "المدينة", "ينبع") else "المنطقة الشرقية",
                industry, f"+9665{random.randint(0,9)}{random.randint(10000000, 99999999)}",
                f"info@{name_ar.lower()}.com.sa",
                f"www.{name_ar.lower()}.com.sa",
                capital, "SAR",
                random.choice([10, 25, 50, 100, 200, 500]),
                pick(["مؤسسة فردية", "شركة ذات مسؤولية محدودة", "شركة مساهمة"]),
                created.date(), created,
            )

            # License per company
            lic_type_idx = random.randint(0, len(LICENSE_TYPES) - 1)
            issue = rdate(2018, 2024)
            expiry = rdate(2025, 2028)
            await conn.execute(
                """INSERT INTO licenses (id, company_id, license_number, license_type, license_type_ar,
                   status, issue_date, expiry_date, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,NOW())""",
                uuid_mod.uuid4(), cid,
                f"{random.randint(100000, 999999)}",
                LICENSE_TYPE_EN[lic_type_idx], LICENSE_TYPES[lic_type_idx],
                pick(["active", "active", "active", "expired", "suspended"]),
                issue.date(), expiry.date(),
            )

            # Golden record per company
            await conn.execute(
                """INSERT INTO golden_records (id, tenant_id, cr_number, company_id, data, confidence_score, is_active, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,true,NOW())""",
                uuid_mod.uuid4(), TID_UUID, cr, cid,
                json.dumps({"name_ar": f"{prefix} {name_ar} {sector_ar}", "industry": industry, "city": city_ar}),
                random.uniform(0.7, 0.99),
            )

        n_companies_actual = len(company_ids)
        print(f"Created {n_companies_actual} companies with licenses and golden records")

        # Create contacts (no tenant_id column)
        n_contacts = counts.get("contacts", 5000)
        contact_ids = []
        for i in range(n_contacts):
            cid = company_ids[i % n_companies_actual]
            is_male = random.random() > 0.4
            first_ar = pick(FIRST_NAMES_AR if is_male else FIRST_NAMES_AR_F)
            last_ar = pick(LAST_NAMES_AR)
            pos_ar, pos_en = pick(POSITIONS)
            en_first = ["Mohamed","Ahmed","Ali","Omar","Khaled","Abdullah","Faisal","Saud","Fahad","Naser"][i % 10]

            ctc_id = uuid_mod.uuid4()
            contact_ids.append(ctc_id)
            await conn.execute(
                """INSERT INTO contacts (id, company_id, name, name_ar, email, phone, mobile,
                   position, position_ar, is_primary, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,NOW())""",
                ctc_id, cid,
                f"{en_first} {last_ar}",
                f"{first_ar} {last_ar}",
                f"{first_ar.lower()}@company{i}.com.sa",
                f"+9665{random.randint(0,9)}{random.randint(10000000, 99999999)}",
                f"+9665{random.randint(0,9)}{random.randint(10000000, 99999999)}",
                pos_en, pos_ar,
                random.random() > 0.7,
            )
        print(f"Created {n_contacts} contacts")

        # Create company_deals (tenant_id=VARCHAR, company_id=VARCHAR)
        n_deals = counts.get("deals", 3000)
        for i in range(n_deals):
            cid = company_ids[i % n_companies_actual]
            ctc_id = contact_ids[i % n_contacts]
            stage_ar, stage_en = pick(DEAL_STAGES)
            amount = random.choice([50000, 100000, 250000, 500000, 1000000, 2500000, 5000000])
            created = rdate(2023, 2025)
            close = created + timedelta(days=random.randint(30, 180))

            await conn.execute(
                """INSERT INTO company_deals (id, tenant_id, company_id, deal_name, amount,
                   currency, status, stage, probability, expected_close_date, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)""",
                str(uuid_mod.uuid4()), TID, str(cid),
                f"Opportunity {i+1} - {stage_en}",
                amount, "SAR",
                pick(["open", "open", "open", "won", "lost"]),
                stage_en, random.choice([10, 25, 50, 75, 90]),
                close.date(), created,
            )
        print(f"Created {n_deals} deals")

        # Create activity_records (id=VARCHAR, tenant_id=VARCHAR)
        n_activities = counts.get("activities", 10000)
        company_id_set = set(company_ids)
        activity_types = [
            ("اجتماع", "Meeting"), ("مكالمة", "Call"), ("بريد إلكتروني", "Email"),
            ("عرض تجاري", "Demo"), ("متابعة", "Follow-up"),
            ("مفاوضات", "Negotiation"), ("توقيع عقد", "Contract Signing"),
            ("زيارة ميدانية", "Site Visit"),
        ]
        for i in range(n_activities):
            entity = random.choice(company_ids + contact_ids)
            entity_type = "company" if entity in company_id_set else "contact"
            act_ar, act_en = pick(activity_types)
            ts = rdate(2024, 2025)

            await conn.execute(
                """INSERT INTO activity_records (id, actor, action, entity_type, entity_id, metadata, tenant_id, timestamp)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
                str(uuid_mod.uuid4()),
                f"user-{random.randint(1, n_users)}",
                act_en.lower().replace(" ", "_"),
                entity_type, str(entity),
                json.dumps({"description_ar": act_ar, "description_en": act_en}),
                TID, ts,
            )
        print(f"Created {n_activities} activities")

        # Timeline entries (1 per company)
        for cid in company_ids:
            await conn.execute(
                """INSERT INTO timeline_entries (entity_type, entity_id, event_type, data, tenant_id, importance, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,NOW())""",
                "company", str(cid),
                pick(["company_created", "company_updated", "license_renewed", "contact_added"]),
                json.dumps({"note": f"Demo seed timeline entry for {cid}"}),
                TID, random.randint(1, 5),
            )
        print(f"Created timeline entries for {len(company_ids)} companies")

    finally:
        await conn.close()

    print()
    print("Demo dataset seeded successfully!")
    print(f"  Users:      {n_users}")
    print(f"  Companies:  {n_companies_actual}")
    print(f"  Contacts:   {n_contacts}")
    print(f"  Deals:      {n_deals}")
    print(f"  Activities: {n_activities}")


async def clear_database():
    import asyncpg

    dsn = "postgresql://salesos:salesos_dev_password@postgres:5432/salesos"
    conn = await asyncpg.connect(dsn)
    TID = "d1e2f3a4-5678-90ab-cdef-1234567890ab"
    TID_UUID = uuid_mod.UUID(TID)

    try:
        tables_varchar = [
            "activity_records", "timeline_entries", "company_deals",
        ]
        tables_uuid = [
            "licenses", "golden_records",
        ]
        for tbl in tables_varchar:
            await conn.execute(f"DELETE FROM {tbl} WHERE tenant_id = $1", TID)
        # contacts has no tenant_id, delete via join
        await conn.execute("DELETE FROM contacts WHERE company_id IN (SELECT id FROM companies WHERE tenant_id = $1)", TID_UUID)
        await conn.execute("DELETE FROM licenses WHERE company_id IN (SELECT id FROM companies WHERE tenant_id = $1)", TID_UUID)
        for tbl in tables_uuid:
            await conn.execute(f"DELETE FROM {tbl} WHERE tenant_id = $1", TID_UUID)
        await conn.execute("DELETE FROM companies WHERE tenant_id = $1", TID_UUID)
        await conn.execute("DELETE FROM users WHERE tenant_id = $1", TID_UUID)
        await conn.execute("DELETE FROM tenants WHERE id = $1", TID_UUID)
        print("Cleared all demo data")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SalesOS Demo Data Seeder")
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--companies", type=int, default=1000)
    parser.add_argument("--contacts", type=int, default=5000)
    parser.add_argument("--deals", type=int, default=3000)
    parser.add_argument("--activities", type=int, default=10000)
    parser.add_argument("--clear", action="store_true", help="Clear all demo data first")
    args = parser.parse_args()

    counts = {
        "users": args.users,
        "companies": args.companies,
        "contacts": args.contacts,
        "deals": args.deals,
        "activities": args.activities,
    }

    if args.clear:
        asyncio.run(clear_database())

    asyncio.run(seed_database(counts))
