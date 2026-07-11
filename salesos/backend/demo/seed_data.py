"""SalesOS — Seed data generator
Generates realistic Saudi companies, opportunities, signals, and decision makers.
Run: python -m demo.seed_data
"""

import json
import random
from datetime import datetime, timedelta

COMPANIES = [
    {"name_ar": "أرامكو السعودية", "name_en": "Saudi Aramco", "cr_number": "1010000001", "city": "الظهران", "region": "المنطقة الشرقية", "industry": "energy", "employees": 70000, "status": "نشط"},
    {"name_ar": "شركة الاتصالات السعودية STC", "name_en": "Saudi Telecom Company", "cr_number": "1010000002", "city": "الرياض", "region": "منطقة الرياض", "industry": "telecom", "employees": 22000, "status": "نشط"},
    {"name_ar": "البنك الأهلي السعودي", "name_en": "SNB", "cr_number": "1010000003", "city": "الرياض", "region": "منطقة الرياض", "industry": "financial", "employees": 18000, "status": "نشط"},
    {"name_ar": "شركة الزامل للاستثمار الصناعي", "name_en": "Zamil Industrial", "cr_number": "1010000004", "city": "الدمام", "region": "المنطقة الشرقية", "industry": "industrial", "employees": 4500, "status": "نشط"},
    {"name_ar": "مجموعة سامبا المالية", "name_en": "Samba Financial Group", "cr_number": "1010000005", "city": "الرياض", "region": "منطقة الرياض", "industry": "financial", "employees": 3200, "status": "نشط"},
    {"name_ar": "شركة المراعي", "name_en": "Almarai", "cr_number": "1010000006", "city": "الرياض", "region": "منطقة الرياض", "industry": "food", "employees": 28000, "status": "نشط"},
    {"name_ar": "شركة سابك", "name_en": "SABIC", "cr_number": "1010000007", "city": "الرياض", "region": "منطقة الرياض", "industry": "petrochemical", "employees": 33000, "status": "نشط"},
    {"name_ar": "مجموعة الطيار للسفر", "name_en": "Al Tayyar Travel", "cr_number": "1010000008", "city": "الرياض", "region": "منطقة الرياض", "industry": "travel", "employees": 2500, "status": "نشط"},
    {"name_ar": "شركة الجرير للتسويق", "name_en": "Jarir Marketing", "cr_number": "1010000009", "city": "الرياض", "region": "منطقة الرياض", "industry": "retail", "employees": 4000, "status": "نشط"},
    {"name_ar": "شركة الكهرباء السعودية", "name_en": "Saudi Electricity", "cr_number": "1010000010", "city": "الرياض", "region": "منطقة الرياض", "industry": "energy", "employees": 35000, "status": "نشط"},
    {"name_ar": "شركة مياهنا", "name_en": "Miahona", "cr_number": "1010000011", "city": "الخبر", "region": "المنطقة الشرقية", "industry": "water", "employees": 800, "status": "نشط"},
    {"name_ar": "مجموعة الحكير", "name_en": "Al Hokair Group", "cr_number": "1010000012", "city": "الرياض", "region": "منطقة الرياض", "industry": "hospitality", "employees": 6500, "status": "نشط"},
    {"name_ar": "شركة تطوير التعليم القابضة", "name_en": "Tatweer Education", "cr_number": "1010000013", "city": "الرياض", "region": "منطقة الرياض", "industry": "education", "employees": 3000, "status": "نشط"},
    {"name_ar": "مجموعة إثراء", "name_en": "Ithra Group", "cr_number": "1010000014", "city": "الظهران", "region": "المنطقة الشرقية", "industry": "energy", "employees": 500, "status": "نشط"},
    {"name_ar": "شركة علم", "name_en": "Alam", "cr_number": "1010000015", "city": "الرياض", "region": "منطقة الرياض", "industry": "technology", "employees": 1800, "status": "نشط"},
    {"name_ar": "شركة أكوا باور", "name_en": "ACWA Power", "cr_number": "1010000016", "city": "الرياض", "region": "منطقة الرياض", "industry": "energy", "employees": 4000, "status": "نشط"},
    {"name_ar": "مجموعة الدكتور سليمان الحبيب", "name_en": "Sulaiman Al Habib Medical", "cr_number": "1010000017", "city": "الرياض", "region": "منطقة الرياض", "industry": "healthcare", "employees": 12000, "status": "نشط"},
    {"name_ar": "شركة أسمنت السعودية", "name_en": "Saudi Cement", "cr_number": "1010000018", "city": "الدمام", "region": "المنطقة الشرقية", "industry": "construction", "employees": 2000, "status": "نشط"},
    {"name_ar": "شركة نماء للكيماويات", "name_en": "Nama Chemicals", "cr_number": "1010000019", "city": "الجبيل", "region": "المنطقة الشرقية", "industry": "petrochemical", "employees": 1200, "status": "نشط"},
    {"name_ar": "شركة هرفي للخدمات الغذائية", "name_en": "Herfy Food Services", "cr_number": "1010000020", "city": "الرياض", "region": "منطقة الرياض", "industry": "food", "employees": 6000, "status": "نشط"},
    {"name_ar": "شركة بحر العرب لتقنية المعلومات", "name_en": "Arabian Sea IT", "cr_number": "1010000021", "city": "جدة", "region": "منطقة مكة المكرمة", "industry": "technology", "employees": 150, "status": "نشط"},
    {"name_ar": "مؤسسة الرواد للتجارة", "name_en": "Al Rawad Trading", "cr_number": "1010000022", "city": "جدة", "region": "منطقة مكة المكرمة", "industry": "retail", "employees": 200, "status": "نشط"},
    {"name_ar": "شركة الخليج للتدريب", "name_en": "Gulf Training", "cr_number": "1010000023", "city": "الخبر", "region": "المنطقة الشرقية", "industry": "education", "employees": 300, "status": "نشط"},
    {"name_ar": "مجموعة المسافة للسياحة", "name_en": "Distance Tourism", "cr_number": "1010000024", "city": "مكة المكرمة", "region": "منطقة مكة المكرمة", "industry": "travel", "employees": 400, "status": "نشط"},
    {"name_ar": "شركة الابتكار للاتصالات", "name_en": "Innovation Telecom", "cr_number": "1010000025", "city": "الرياض", "region": "منطقة الرياض", "industry": "telecom", "employees": 600, "status": "نشط"},
    {"name_ar": "مستشفى الملك فيصل التخصصي", "name_en": "King Faisal Specialist Hospital", "cr_number": "1010000026", "city": "الرياض", "region": "منطقة الرياض", "industry": "healthcare", "employees": 9000, "status": "نشط"},
    {"name_ar": "شركة السيف للهندسة", "name_en": "Al Saif Engineering", "cr_number": "1010000027", "city": "الدمام", "region": "المنطقة الشرقية", "industry": "construction", "employees": 3500, "status": "نشط"},
    {"name_ar": "شركة رؤية المدينة القابضة", "name_en": "Vision City Holding", "cr_number": "1010000028", "city": "المدينة المنورة", "region": "منطقة المدينة المنورة", "industry": "real_estate", "employees": 1000, "status": "نشط"},
    {"name_ar": "مؤسسة الباحة للتجارة", "name_en": "Al Baha Trading", "cr_number": "1010000029", "city": "الباحة", "region": "منطقة الباحة", "industry": "retail", "employees": 120, "status": "نشط"},
    {"name_ar": "شركة تبوك للتنمية الزراعية", "name_en": "Tabuk Agricultural", "cr_number": "1010000030", "city": "تبوك", "region": "منطقة تبوك", "industry": "agriculture", "employees": 800, "status": "نشط"},
    {"name_ar": "شركة الجوف للطاقة المتجددة", "name_en": "Al Jouf Renewable Energy", "cr_number": "1010000031", "city": "سكاكا", "region": "منطقة الجوف", "industry": "energy", "employees": 350, "status": "نشط"},
    {"name_ar": "شركة نجران للصناعات الغذائية", "name_en": "Najran Food Industries", "cr_number": "1010000032", "city": "نجران", "region": "منطقة نجران", "industry": "food", "employees": 500, "status": "نشط"},
    {"name_ar": "مجموعة عسير القابضة", "name_en": "Asir Holding", "cr_number": "1010000033", "city": "أبها", "region": "منطقة عسير", "industry": "hospitality", "employees": 2000, "status": "نشط"},
    {"name_ar": "شركة حائل للتنمية", "name_en": "Hail Development", "cr_number": "1010000034", "city": "حائل", "region": "منطقة حائل", "industry": "real_estate", "employees": 250, "status": "نشط"},
    {"name_ar": "شركة الحدود الشمالية للتعدين", "name_en": "Northern Borders Mining", "cr_number": "1010000035", "city": "عرعر", "region": "المنطقة الشمالية", "industry": "mining", "employees": 450, "status": "نشط"},
    {"name_ar": "مجموعة جازان الاقتصادية", "name_en": "Jazan Economic Group", "cr_number": "1010000036", "city": "جازان", "region": "منطقة جازان", "industry": "industrial", "employees": 700, "status": "نشط"},
    {"name_ar": "شركة القصيم القابضة", "name_en": "Qassim Holding", "cr_number": "1010000037", "city": "بريدة", "region": "منطقة القصيم", "industry": "agriculture", "employees": 600, "status": "نشط"},
]

SIGNAL_TYPES = ['hiring', 'expansion', 'partnership', 'contract', 'regulation', 'market', 'financial', 'news']
SIGNAL_TITLES = {
    'hiring': ['توظيف {count} موظف جديد', 'فتح {count} وظيفة في التقنية', 'استقطاب كفاءات'],
    'expansion': ['افتتاح فرع جديد في {city}', 'التوسع في {region}', 'خطة توسعية في قطاع {industry}'],
    'partnership': ['شراكة استراتيجية مع {partner}', 'اتفاقية تعاون مع {partner}', 'تحالف استراتيجي'],
    'contract': ['فوز بعقد حكومي بقيمة {value}', 'توقيع عقد مع {partner}', 'تجديد عقد استراتيجي'],
    'regulation': ['امتثال للوائح الجديدة', 'تحديث التراخيص', 'موافقة تنظيمية جديدة'],
    'market': ['ارتفاع الطلب على منتجات {industry}', 'توسع حصة سوقية', 'دخول سوق جديد'],
    'financial': ['نتائج مالية قياسية', 'ارتفاع الأرباح {percent}%', 'توزيع أرباح على المساهمين'],
    'news': ['إعلان مهم من {company}', 'جولة تمويلية جديدة', 'تغيير في الإدارة التنفيذية'],
}

PARTNERS = ['أرامكو', 'STC', 'وزارة الاستثمار', 'صندوق الاستثمارات العامة', 'الهيئة الملكية', 'شركة مباني', 'مجموعة السريع']
USERS = [
    {"name": "أحمد السلمي", "role": "مدير المبيعات", "email": "a@salesos.com"},
    {"name": "نورة القحطاني", "role": "مدير الحسابات", "email": "n@salesos.com"},
    {"name": "فهد العتيبي", "role": "مندوب مبيعات", "email": "f@salesos.com"},
    {"name": "سارة الدوسري", "role": "مدير التسويق", "email": "s@salesos.com"},
]

def seed_data():
    """Generate seed data as JSON files."""
    print("🌱 Seeding SalesOS data...")
    
    now = datetime.now()
    signals = []
    decision_makers = []
    opportunities = []
    tasks = []
    
    for i, company in enumerate(COMPANIES):
        # Signals per company (1-3)
        for _ in range(random.randint(1, 3)):
            sig_type = random.choice(SIGNAL_TYPES)
            days_ago = random.randint(0, 30)
            titles = SIGNAL_TITLES[sig_type]
            title = random.choice(titles).format(
                count=random.randint(10, 500),
                city=company["city"],
                region=company["region"],
                industry=company["industry"],
                partner=random.choice(PARTNERS),
                company=company["name_ar"],
                value=f"{random.randint(500, 5000)}K",
                percent=random.randint(10, 50),
            )
            signals.append({
                "company_id": i + 1,
                "type": sig_type,
                "title": title,
                "severity": random.choices(['low', 'medium', 'high', 'critical'], weights=[30, 40, 25, 5])[0],
                "ai_confidence": round(random.uniform(0.6, 0.98), 2),
                "timestamp": (now - timedelta(days=days_ago)).isoformat(),
            })
        
        # Decision makers (1-3 per company)
        for _ in range(random.randint(1, 3)):
            decision_makers.append({
                "company_id": i + 1,
                "name": f"شخص {random.randint(100, 999)}",
                "role": random.choice(["CEO", "CTO", "CFO", "مدير المشتريات", "مدير التقنية", "نائب الرئيس"]),
                "influence": random.choice(["low", "medium", "high"]),
                "connected": random.choice([True, False]),
            })
        
        # Opportunities (30 companies have active opps)
        if i < 30:
            stage = random.choices(
                ['identified', 'qualifying', 'developing', 'proposing', 'negotiating'],
                weights=[15, 25, 30, 20, 10]
            )[0]
            value = random.randint(200000, 5000000)
            opportunities.append({
                "company_id": i + 1,
                "company_name": company["name_ar"],
                "title": f"فرصة {company['industry']} — {company['name_ar'][:20]}",
                "stage": stage,
                "estimated_value": value,
                "confidence": round(random.uniform(0.3, 0.95), 2),
                "buying_intent": round(random.uniform(0.3, 0.95), 2),
                "relationship_strength": round(random.uniform(0.3, 0.95), 2),
                "created_at": (now - timedelta(days=random.randint(1, 90))).isoformat(),
            })
        
        # Tasks (some companies have tasks)
        if random.random() < 0.4:
            tasks.append({
                "company_id": i + 1,
                "company_name": company["name_ar"],
                "title": f"متابعة {company['name_ar'][:15]}",
                "priority": random.choice(['critical', 'high', 'medium', 'low']),
                "source": random.choice(['nba', 'manual', 'meeting']),
            })

    # Write seed files
    output = {
        "companies": COMPANIES,
        "signals": signals,
        "decision_makers": decision_makers,
        "opportunities": opportunities,
        "tasks": tasks,
        "generated_at": now.isoformat(),
        "total": {
            "companies": len(COMPANIES),
            "signals": len(signals),
            "decision_makers": len(decision_makers),
            "opportunities": len(opportunities),
            "tasks": len(tasks),
        }
    }
    
    print(f"  ✓ {len(COMPANIES)} companies")
    print(f"  ✓ {len(signals)} signals")
    print(f"  ✓ {len(decision_makers)} decision makers")
    print(f"  ✓ {len(opportunities)} opportunities")
    print(f"  ✓ {len(tasks)} tasks")
    print(f"\n📁 Written to demo/data.json")
    
    import os
    os.makedirs("demo", exist_ok=True)
    with open("demo/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return output

if __name__ == "__main__":
    data = seed_data()
    print(f"\n✅ Done! {data['total']['companies']} companies, {data['total']['signals']} signals, {data['total']['opportunities']} opportunities")
