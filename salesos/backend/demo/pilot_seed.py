"""SalesOS - Pilot seed data generator
Extends seed_data.py with 5 pilot companies, decision makers, opportunities,
signals, timeline events, and tasks for the Pilot Launch program.

Run: python -m backend.demo.pilot_seed
"""

import io
import json
import random
import os
import sys
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PILOT_TENANT_ID = "pilot_tenant"

PILOT_COMPANIES = [
    {
        "tenant_id": PILOT_TENANT_ID,
        "name_ar": "شركة طاقة الخليج",
        "name_en": "Gulf Energy Co.",
        "cr_number": "3010000001",
        "city": "الرياض",
        "region": "منطقة الرياض",
        "industry": "energy",
        "employees": 1200,
        "status": "نشط",
        "description": "شركة رائدة في قطاع الطاقة والخدمات النفطية، تقدم حلولاً متكاملة لتحلية المياه وتوليد الطاقة.",
    },
    {
        "tenant_id": PILOT_TENANT_ID,
        "name_ar": "شركة أثير للاتصالات",
        "name_en": "Atheer Telecom Co.",
        "cr_number": "3010000002",
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "industry": "telecom",
        "employees": 850,
        "status": "نشط",
        "description": "مزود خدمات اتصالات وحلول رقمية للشركات، متخصص في البنية التحتية للاتصالات والأمن السيبراني.",
    },
    {
        "tenant_id": PILOT_TENANT_ID,
        "name_ar": "بنك الراجحي المالي",
        "name_en": "Al Rajhi Financial",
        "cr_number": "3010000003",
        "city": "الدمام",
        "region": "المنطقة الشرقية",
        "industry": "financial",
        "employees": 2100,
        "status": "نشط",
        "description": "مجموعة مالية تقدم خدمات مصرفية واستثمارية وتمويلية للشركات في المملكة.",
    },
    {
        "tenant_id": PILOT_TENANT_ID,
        "name_ar": "مستشفى السلام الطبي",
        "name_en": "Al Salam Medical Group",
        "cr_number": "3010000004",
        "city": "الخبر",
        "region": "المنطقة الشرقية",
        "industry": "healthcare",
        "employees": 1400,
        "status": "نشط",
        "description": "مجموعة طبية رائدة تضم 3 مستشفيات و 8 عيادات متخصصة في المنطقة الشرقية.",
    },
    {
        "tenant_id": PILOT_TENANT_ID,
        "name_ar": "شركة بيانات التقنية",
        "name_en": "Bayanat Tech Solutions",
        "cr_number": "3010000005",
        "city": "الجبيل",
        "region": "المنطقة الشرقية",
        "industry": "technology",
        "employees": 620,
        "status": "نشط",
        "description": "شركة تقنية سعودية متخصصة في حلول البيانات الضخمة والذكاء الاصطناعي وإنترنت الأشياء.",
    },
]

DECISION_MAKERS = {
    1: [
        {"name": "د. يوسف العتيبي", "role": "CEO", "influence": "high", "connected": True, "email": "y.otaibi@gulfenergy.sa"},
        {"name": "م. سعد الغامدي", "role": "CTO", "influence": "high", "connected": True, "email": "s.ghamdi@gulfenergy.sa"},
        {"name": "أ. خالد المطيري", "role": "مدير المشتريات", "influence": "medium", "connected": False, "email": "k.almutairi@gulfenergy.sa"},
    ],
    2: [
        {"name": "أ. نورة الزهراني", "role": "CEO", "influence": "high", "connected": True, "email": "n.zahrani@atheertelecom.sa"},
        {"name": "م. فيصل الأحمدي", "role": "CTO", "influence": "high", "connected": True, "email": "f.alahmadi@atheertelecom.sa"},
    ],
    3: [
        {"name": "أ. عبدالله التميمي", "role": "CEO", "influence": "high", "connected": True, "email": "a.tamimi@alrajhi-financial.sa"},
        {"name": "أ. محمد البجاد", "role": "CFO", "influence": "high", "connected": True, "email": "m.albadjad@alrajhi-financial.sa"},
        {"name": "أ. سارة المبارك", "role": "مدير التقنية", "influence": "medium", "connected": False, "email": "s.almubarak@alrajhi-financial.sa"},
    ],
    4: [
        {"name": "د. هاني باحارث", "role": "CEO", "influence": "high", "connected": True, "email": "h.baharth@alsalam-medical.sa"},
        {"name": "أ. منال الشمري", "role": "مدير المشتريات", "influence": "medium", "connected": True, "email": "m.alshamri@alsalam-medical.sa"},
    ],
    5: [
        {"name": "م. عبدالعزيز السحيباني", "role": "CEO", "influence": "high", "connected": True, "email": "a.alsohaibani@bayanat-tech.sa"},
        {"name": "أ. ريم الحارثي", "role": "CTO", "influence": "high", "connected": True, "email": "r.alharthi@bayanat-tech.sa"},
        {"name": "م. تركي الدوسري", "role": "مدير المبيعات", "influence": "medium", "connected": False, "email": "t.aldosari@bayanat-tech.sa"},
    ],
}

OPPORTUNITIES = [
    {
        "company_id": 1, "company_name": "شركة طاقة الخليج",
        "title": "فرصة حلول إدارة الطاقة — طاقة الخليج",
        "stage": "proposing", "estimated_value": 3_500_000, "confidence": 0.72,
        "buying_intent": 0.80, "relationship_strength": 0.65,
        "description": "تنفيذ نظام إدارة الطاقة الذكي لتحسين كفاءة استهلاك الطاقة في 5 منشآت.",
    },
    {
        "company_id": 1, "company_name": "شركة طاقة الخليج",
        "title": "خدمات استشارية للتحول الرقمي — طاقة الخليج",
        "stage": "qualifying", "estimated_value": 1_200_000, "confidence": 0.45,
        "buying_intent": 0.50, "relationship_strength": 0.55,
        "description": "استشارات التحول الرقمي وتطوير البنية التحتية التقنية.",
    },
    {
        "company_id": 1, "company_name": "شركة طاقة الخليج",
        "title": "حلول الأمن السيبراني للبنية التحتية — طاقة الخليج",
        "stage": "identified", "estimated_value": 850_000, "confidence": 0.30,
        "buying_intent": 0.35, "relationship_strength": 0.40,
        "description": "تطبيق حلول الأمن السيبراني لحماية البنية التحتية الحيوية للطاقة.",
    },
    {
        "company_id": 2, "company_name": "شركة أثير للاتصالات",
        "title": "منصة إدارة علاقات العملاء المتكاملة — أثير",
        "stage": "negotiating", "estimated_value": 2_800_000, "confidence": 0.88,
        "buying_intent": 0.90, "relationship_strength": 0.82,
        "description": "تنفيذ منصة CRM متكاملة مع حلول الذكاء الاصطناعي لتحليل العملاء.",
    },
    {
        "company_id": 2, "company_name": "شركة أثير للاتصالات",
        "title": "خدمات الحوسبة السحابية — أثير",
        "stage": "developing", "estimated_value": 900_000, "confidence": 0.55,
        "buying_intent": 0.60, "relationship_strength": 0.70,
        "description": "ترحيل البنية التحتية للاتصالات إلى الحوسبة السحابية.",
    },
    {
        "company_id": 2, "company_name": "شركة أثير للاتصالات",
        "title": "نظام الفوترة الآلي — أثير",
        "stage": "qualifying", "estimated_value": 450_000, "confidence": 0.38,
        "buying_intent": 0.45, "relationship_strength": 0.50,
        "description": "أتمتة نظام الفوترة والتحصيل للعملاء.",
    },
    {
        "company_id": 3, "company_name": "بنك الراجحي المالي",
        "title": "منصة التحليل المالي الذكي — الراجحي المالي",
        "stage": "proposing", "estimated_value": 5_000_000, "confidence": 0.78,
        "buying_intent": 0.85, "relationship_strength": 0.70,
        "description": "تطوير منصة تحليل مالي تعتمد على الذكاء الاصطناعي للتداول والاستثمار.",
    },
    {
        "company_id": 3, "company_name": "بنك الراجحي المالي",
        "title": "نظام إدارة المخاطر المؤسسية — الراجحي المالي",
        "stage": "developing", "estimated_value": 2_100_000, "confidence": 0.60,
        "buying_intent": 0.65, "relationship_strength": 0.60,
        "description": "تنفيذ نظام متكامل لإدارة المخاطر المالية والتشغيلية.",
    },
    {
        "company_id": 4, "company_name": "مستشفى السلام الطبي",
        "title": "نظام إدارة المرضى الرقمي — السلام الطبي",
        "stage": "negotiating", "estimated_value": 1_800_000, "confidence": 0.85,
        "buying_intent": 0.88, "relationship_strength": 0.78,
        "description": "تطبيق نظام إدارة المرضى الإلكتروني (EHR) في 3 مستشفيات.",
    },
    {
        "company_id": 4, "company_name": "مستشفى السلام الطبي",
        "title": "حلول التطبيب عن بعد — السلام الطبي",
        "stage": "qualifying", "estimated_value": 750_000, "confidence": 0.40,
        "buying_intent": 0.48, "relationship_strength": 0.50,
        "description": "منصة التطبيب عن بعد والاستشارات الطبية عن بُعد.",
    },
    {
        "company_id": 4, "company_name": "مستشفى السلام الطبي",
        "title": "برنامج الولاء للمرضى — السلام الطبي",
        "stage": "identified", "estimated_value": 300_000, "confidence": 0.25,
        "buying_intent": 0.30, "relationship_strength": 0.35,
        "description": "تطوير برنامج ولاء رقمي لتحسين الاحتفاظ بالمرضى.",
    },
    {
        "company_id": 5, "company_name": "شركة بيانات التقنية",
        "title": "منصة تحليل البيانات الضخمة — بيانات",
        "stage": "proposing", "estimated_value": 4_200_000, "confidence": 0.82,
        "buying_intent": 0.88, "relationship_strength": 0.75,
        "description": "بناء منصة تحليل بيانات ضخمة تدعم قرارات الأعمال بالذكاء الاصطناعي.",
    },
    {
        "company_id": 5, "company_name": "شركة بيانات التقنية",
        "title": "حلول إنترنت الأشياء الصناعي — بيانات",
        "stage": "developing", "estimated_value": 1_500_000, "confidence": 0.58,
        "buying_intent": 0.62, "relationship_strength": 0.55,
        "description": "تطبيق حلول IoT لمراقبة وتحسين العمليات الصناعية.",
    },
]

SIGNALS = [
    # Company 1 — Gulf Energy
    {"company_id": 1, "type": "hiring", "severity": "high",
     "title": "توظيف 45 مهندس طاقة متجددة وخبراء تحول رقمي",
     "ai_confidence": 0.92, "days_ago": 5,
     "details": "إعلان توظيف كبير في مجالات الطاقة المتجددة والتحول الرقمي."},
    {"company_id": 1, "type": "contract", "severity": "critical",
     "title": "فوز بعقد حكومي بقيمة 85 مليون ريال لتطوير شبكة الكهرباء",
     "ai_confidence": 0.95, "days_ago": 3,
     "details": "عقد مع وزارة الطاقة لتحديث وتطوير شبكات الكهرباء في المنطقة الوسطى."},
    {"company_id": 1, "type": "expansion", "severity": "medium",
     "title": "التوسع في المنطقة الغربية بافتتاح مركز عمليات جديد",
     "ai_confidence": 0.78, "days_ago": 12,
     "details": "افتتاح مركز عمليات متكامل في جدة لخدمة العملاء في المنطقة الغربية."},
    {"company_id": 1, "type": "market", "severity": "high",
     "title": "ارتفاع الطلب على حلول إدارة الطاقة بنسبة 35%",
     "ai_confidence": 0.85, "days_ago": 7,
     "details": "زيادة الطلب على حلول إدارة الطاقة بسبب رفع الدعم عن الكهرباء."},
    # Company 2 — Atheer Telecom
    {"company_id": 2, "type": "hiring", "severity": "high",
     "title": "استقطاب 30 كفاءة في الأمن السيبراني والذكاء الاصطناعي",
     "ai_confidence": 0.90, "days_ago": 2,
     "details": "حملة توظيف كوادر متخصصة في الأمن السيبراني وتقنيات الذكاء الاصطناعي."},
    {"company_id": 2, "type": "partnership", "severity": "high",
     "title": "شراكة استراتيجية مع وزارة الاتصالات لتطوير البنية الرقمية",
     "ai_confidence": 0.88, "days_ago": 8,
     "details": "اتفاقية شراكة مع وزارة الاتصالات وتقنية المعلومات لتطوير البنية التحتية الرقمية."},
    {"company_id": 2, "type": "contract", "severity": "critical",
     "title": "توقيع عقد حكومي بقيمة 120 مليون ريال لتأمين شبكات حكومية",
     "ai_confidence": 0.96, "days_ago": 1,
     "details": "عقد مع هيئة الحكومة الرقمية لتأمين شبكات 15 جهة حكومية."},
    {"company_id": 2, "type": "expansion", "severity": "medium",
     "title": "افتتاح 3 مكاتب جديدة في المنطقة الشرقية والشمالية",
     "ai_confidence": 0.75, "days_ago": 15,
     "details": "افتتاح مكاتب جديدة في الدمام وحائل وتبوك."},
    # Company 3 — Al Rajhi Financial
    {"company_id": 3, "type": "hiring", "severity": "high",
     "title": "توظيف 50 محلل مالي ومتخصص في التكنولوجيا المالية",
     "ai_confidence": 0.91, "days_ago": 6,
     "details": "أكبر حملة توظيف في تاريخ البنك في مجالات التحليل المالي والتقنية."},
    {"company_id": 3, "type": "regulation", "severity": "critical",
     "title": "موافقة البنك المركزي السعودي على إطلاق منصة التمويل الرقمي",
     "ai_confidence": 0.97, "days_ago": 4,
     "details": "حصل على موافقة نظامية من البنك المركزي لإطلاق منصة تمويل رقمية متكاملة."},
    {"company_id": 3, "type": "market", "severity": "high",
     "title": "توسع حصة سوقية في التمويل المؤسسي بنسبة 22%",
     "ai_confidence": 0.84, "days_ago": 10,
     "details": "نمو حصة البنك في سوق التمويل المؤسسي مدعوم بحلول رقمية مبتكرة."},
    {"company_id": 3, "type": "financial", "severity": "high",
     "title": "نتائج مالية قياسية بارتفاع الأرباح 28%",
     "ai_confidence": 0.93, "days_ago": 2,
     "details": "أرباح قياسية للربع الثاني مدعومة بنمو التمويل والاستثمارات."},
    # Company 4 — Al Salam Medical
    {"company_id": 4, "type": "hiring", "severity": "high",
     "title": "توظيف 120 ممارس صحي وإداري في 3 مستشفيات جديدة",
     "ai_confidence": 0.89, "days_ago": 9,
     "details": "توظيف أطباء وممرضين وإداريين لاستيعاب التوسع في المستشفيات الجديدة."},
    {"company_id": 4, "type": "expansion", "severity": "critical",
     "title": "افتتاح مستشفيين جديدين في الرياض وجدة بتكلفة 500 مليون ريال",
     "ai_confidence": 0.94, "days_ago": 4,
     "details": "استثمار ضخم في مستشفيين جديدين بسعة 300 سرير لكل مستشفى."},
    {"company_id": 4, "type": "contract", "severity": "high",
     "title": "فوز بعقد تشغيل مستشفى حكومي لمدة 5 سنوات",
     "ai_confidence": 0.86, "days_ago": 11,
     "details": "عقد مع وزارة الصحة لتشغيل وإدارة مستشفى حكومي في المنطقة الشرقية."},
    {"company_id": 4, "type": "partnership", "severity": "medium",
     "title": "شراكة مع مستشفى كليفلاند كلينك للاستشارات الطبية",
     "ai_confidence": 0.72, "days_ago": 18,
     "details": "اتفاقية تعاون طبي مع مستشفى كليفلاند كلينك الأمريكية."},
    # Company 5 — Bayanat Tech
    {"company_id": 5, "type": "hiring", "severity": "high",
     "title": "استقطاب 60 مهندس برمجيات ومتخصص ذكاء اصطناعي",
     "ai_confidence": 0.93, "days_ago": 3,
     "details": "حملة توظيف كبرى لمهندسي برمجيات وخبراء ذكاء اصطناعي وتعلم آلة."},
    {"company_id": 5, "type": "contract", "severity": "critical",
     "title": "فوز بعقد حكومي ضخم بقيمة 200 مليون ريال لمنصة بيانات وطنية",
     "ai_confidence": 0.97, "days_ago": 1,
     "details": "عقد مع الهيئة السعودية للبيانات والذكاء الاصطناعي (SDAIA) لبناء منصة البيانات الوطنية."},
    {"company_id": 5, "type": "expansion", "severity": "high",
     "title": "التوسع في السوق الإماراتية بافتتاح مقر إقليمي في دبي",
     "ai_confidence": 0.88, "days_ago": 6,
     "details": "افتتاح مقر إقليمي في مركز دبي المالي العالمي (DIFC)."},
    {"company_id": 5, "type": "partnership", "severity": "high",
     "title": "شراكة استراتيجية مع Google Cloud لتطوير حلول الذكاء الاصطناعي",
     "ai_confidence": 0.91, "days_ago": 10,
     "details": "اتفاقية شراكة مع Google Cloud لتطوير وتقديم حلول ذكاء اصطناعي متقدمة."},
]

TIMELINE_EVENTS = [
    {"company_id": 1, "event_type": "meeting", "title": "اجتماع عرض تقديمي مع CEO وCTO",
     "description": "تقديم عرض حلول إدارة الطاقة الذكية", "days_ago": 2, "user": "نورة القحطاني"},
    {"company_id": 1, "event_type": "email", "title": "إرسال عرض سعر تفصيلي",
     "description": "إرسال عرض السعر النهائي لمشروع إدارة الطاقة", "days_ago": 4, "user": "أحمد السلمي"},
    {"company_id": 1, "event_type": "call", "title": "مكالمة متابعة مع مدير المشتريات",
     "description": "مناقشة تفاصيل العقد والجدول الزمني", "days_ago": 7, "user": "أحمد السلمي"},
    {"company_id": 2, "event_type": "meeting", "title": "اجتماع مجلس الإدارة عرض مشروع CRM",
     "description": "عرض مشروع CRM على مجلس الإدارة وحصل على موافقة مبدئية", "days_ago": 1, "user": "فهد العتيبي"},
    {"company_id": 2, "event_type": "email", "title": "إرسال اتفاقية مستوى الخدمة (SLA)",
     "description": "إرسال مسودة اتفاقية مستوى الخدمة للمراجعة", "days_ago": 5, "user": "فهد العتيبي"},
    {"company_id": 3, "event_type": "meeting", "title": "اجتماع مع فريق التقنية لمنصة التحليل المالي",
     "description": "مناقشة المتطلبات التقنية لمنصة التحليل المالي الذكي", "days_ago": 3, "user": "نورة القحطاني"},
    {"company_id": 3, "event_type": "call", "title": "مكالمة تحديد نطاق العمل مع CFO",
     "description": "الاتفاق على نطاق العمل والجدول الزمني للمشروع", "days_ago": 8, "user": "أحمد السلمي"},
    {"company_id": 3, "event_type": "demo", "title": "عرض توضيحي لنظام إدارة المخاطر",
     "description": "تقديم عرض توضيحي مباشر لنظام إدارة المخاطر", "days_ago": 10, "user": "فهد العتيبي"},
    {"company_id": 4, "event_type": "meeting", "title": "اجتماع توقيع العقد لنظام إدارة المرضى",
     "description": "توقيع العقد النهائي لنظام EHR بعد 3 أشهر من المفاوضات", "days_ago": 1, "user": "أحمد السلمي"},
    {"company_id": 4, "event_type": "demo", "title": "عرض توضيحي لحلول التطبيب عن بعد",
     "description": "تقديم عرض توضيحي لفريق تقنية المعلومات", "days_ago": 6, "user": "سارة الدوسري"},
    {"company_id": 4, "event_type": "email", "title": "إرسال دراسة الجدوى الاقتصادية",
     "description": "إرسال دراسة الجدوى لمشروع التطبيب عن بعد", "days_ago": 12, "user": "نورة القحطاني"},
    {"company_id": 5, "event_type": "meeting", "title": "اجتماع استراتيجي مع CEO وCTO",
     "description": "مناقشة الشراكة الإستراتيجية لمنصة البيانات الضخمة", "days_ago": 2, "user": "أحمد السلمي"},
    {"company_id": 5, "event_type": "demo", "title": "عرض تقني معمق لمنصة التحليل",
     "description": "تقديم عرض تقني معمق لمدة 3 ساعات لفريق بيانات", "days_ago": 5, "user": "فهد العتيبي"},
]

TASKS = [
    {"company_id": 1, "priority": "high", "source": "nba",
     "title": "متابعة طلب العرض الرسمي لمشروع إدارة الطاقة"},
    {"company_id": 1, "priority": "medium", "source": "manual",
     "title": "إعداد عرض الأمن السيبراني للبنية التحتية"},
    {"company_id": 2, "priority": "critical", "source": "nba",
     "title": "إنهاء مفاوضات العقد النهائي لمنصة CRM"},
    {"company_id": 2, "priority": "high", "source": "meeting",
     "title": "متابعة طلب الحصول على موافقة ميزانية المشروع السحابي"},
    {"company_id": 3, "priority": "high", "source": "nba",
     "title": "تقديم العرض النهائي لمنصة التحليل المالي الذكي"},
    {"company_id": 3, "priority": "medium", "source": "manual",
     "title": "ترتيب اجتماع مع فريق المخاطر لنظام إدارة المخاطر"},
    {"company_id": 4, "priority": "critical", "source": "nba",
     "title": "بدء تنفيذ المرحلة الأولى لنظام إدارة المرضى"},
    {"company_id": 4, "priority": "low", "source": "manual",
     "title": "إعداد كتيب التعريف بحلول التطبيب عن بعد"},
    {"company_id": 5, "priority": "high", "source": "nba",
     "title": "إعداد الرد على طلب العقد الحكومي لمنصة البيانات"},
    {"company_id": 5, "priority": "medium", "source": "meeting",
     "title": "متابعة اتفاقية الشراكة مع Google Cloud"},
]

OPPORTUNITY_STAGES = [
    "identified", "qualifying", "developing", "proposing", "negotiating"
]


def seed_pilot_data(base_dir: str | None = None):
    """Generate pilot seed data as JSON files."""
    now = datetime.now()
    print("=" * 60)
    print("  SalesOS Pilot Seed Generator")
    print("=" * 60)
    print(f"  Tenant: {PILOT_TENANT_ID}")
    print(f"  Companies: {len(PILOT_COMPANIES)}")
    print()

    # ── Decision makers ──
    decision_makers_out = []
    for cid, dms in DECISION_MAKERS.items():
        for dm in dms:
            decision_makers_out.append({
                "tenant_id": PILOT_TENANT_ID,
                "company_id": cid,
                "name": dm["name"],
                "role": dm["role"],
                "influence": dm["influence"],
                "connected": dm["connected"],
                "email": dm["email"],
            })
    print(f"  [OK] {len(decision_makers_out)} decision makers")

    # ── Opportunities ──
    opportunities_out = []
    for opp in OPPORTUNITIES:
        opportunities_out.append({
            "tenant_id": PILOT_TENANT_ID,
            "company_id": opp["company_id"],
            "company_name": opp["company_name"],
            "title": opp["title"],
            "stage": opp["stage"],
            "estimated_value": opp["estimated_value"],
            "confidence": opp["confidence"],
            "buying_intent": opp["buying_intent"],
            "relationship_strength": opp["relationship_strength"],
            "description": opp["description"],
            "created_at": (now - timedelta(days=random.randint(15, 60))).isoformat(),
            "currency": "SAR",
        })
    print(f"  [OK] {len(opportunities_out)} opportunities")

    # ── Signals ──
    signals_out = []
    for sig in SIGNALS:
        signals_out.append({
            "tenant_id": PILOT_TENANT_ID,
            "company_id": sig["company_id"],
            "type": sig["type"],
            "title": sig["title"],
            "severity": sig["severity"],
            "ai_confidence": sig["ai_confidence"],
            "timestamp": (now - timedelta(days=sig["days_ago"])).isoformat(),
            "details": sig["details"],
        })
    print(f"  [OK] {len(signals_out)} signals")

    # ── Timeline events ──
    timeline_out = []
    for evt in TIMELINE_EVENTS:
        timeline_out.append({
            "tenant_id": PILOT_TENANT_ID,
            "company_id": evt["company_id"],
            "event_type": evt["event_type"],
            "title": evt["title"],
            "description": evt["description"],
            "timestamp": (now - timedelta(days=evt["days_ago"])).isoformat(),
            "user": evt["user"],
        })
    print(f"  [OK] {len(timeline_out)} timeline events")

    # ── Tasks ──
    tasks_out = []
    for task in TASKS:
        tasks_out.append({
            "tenant_id": PILOT_TENANT_ID,
            "company_id": task["company_id"],
            "company_name": PILOT_COMPANIES[task["company_id"] - 1]["name_ar"],
            "title": task["title"],
            "priority": task["priority"],
            "source": task["source"],
            "created_at": (now - timedelta(days=random.randint(1, 10))).isoformat(),
            "status": random.choice(["pending", "in_progress", "completed"]),
        })
    print(f"  [OK] {len(tasks_out)} tasks")

    # ── Assemble output ──
    output = {
        "tenant_id": PILOT_TENANT_ID,
        "companies": PILOT_COMPANIES,
        "decision_makers": decision_makers_out,
        "opportunities": opportunities_out,
        "signals": signals_out,
        "timeline": timeline_out,
        "tasks": tasks_out,
        "generated_at": now.isoformat(),
        "total": {
            "companies": len(PILOT_COMPANIES),
            "decision_makers": len(decision_makers_out),
            "opportunities": len(opportunities_out),
            "signals": len(signals_out),
            "timeline": len(timeline_out),
            "tasks": len(tasks_out),
        }
    }

    # ── Summary ──
    print()
    print("  +--------------+------+")
    print("  | Metric       | Count|")
    print("  +--------------+------+")
    for key, val in output["total"].items():
        print(f"  | {key:12s} | {val:4d} |")
    print("  +--------------+------+")

    # ── Write file ──
    demo_dir = base_dir or os.path.join(os.path.dirname(__file__))
    os.makedirs(demo_dir, exist_ok=True)
    output_path = os.path.join(demo_dir, "pilot_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  [FILE] Written to: {output_path}")

    return output


def print_nba_summary(data: dict):
    """Print a next-best-action style summary for each pilot company."""
    print()
    print("=" * 60)
    print("  NBA Decision Evaluation — Pilot Companies")
    print("=" * 60)
    for company in data["companies"]:
        cid = data["companies"].index(company) + 1
        opps = [o for o in data["opportunities"] if o["company_id"] == cid]
        signals = [s for s in data["signals"] if s["company_id"] == cid]
        dms = [d for d in data["decision_makers"] if d["company_id"] == cid]
        top_opp = max(opps, key=lambda x: x["estimated_value"]) if opps else None

        print()
        print(f"  == {company['name_en']} (ID: {cid}) ==")
        print(f"     Industry: {company['industry']}  |  City: {company['city']}")
        if top_opp:
            print(f"     Top Opportunity: {top_opp['title']}")
            print(f"     Value: SAR {top_opp['estimated_value']:,}  |  Stage: {top_opp['stage']}")
            print(f"     Confidence: {top_opp['confidence']:.0%}  |  Buying Intent: {top_opp['buying_intent']:.0%}")
        print(f"     Key Signals: {', '.join(s['type'] for s in signals[:3])}")
        print(f"     Decision Makers: {', '.join(d['name'] for d in dms)}")
        confidence_avg = sum(s["ai_confidence"] for s in signals) / len(signals) if signals else 0
        print(f"     Signal AI Confidence: {confidence_avg:.0%} average")
        engagement = top_opp["relationship_strength"] if top_opp else 0.5
        print(f"     Engagement Score: {engagement:.0%}")


if __name__ == "__main__":
    data = seed_pilot_data()
    print_nba_summary(data)
    print()
    print("  [DONE] Pilot data ready. Run .\\pilot-onboard.ps1 to verify deployment.")
