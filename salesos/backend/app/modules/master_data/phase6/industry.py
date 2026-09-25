"""Phase 6 — Industry normalization.

Contract: raw industry is kept IMMUTABLE (never overwritten on
md_global_companies.industry); normalized industry is stored SEPARATELY
(md_industry_normalization). Normalization is deterministic, mapping raw
free-text industry strings to a canonical bucket + optional ISIC-ish code.

No external API. No fabrication. Unmapped values stay raw (normalized == raw
cleaned), so we never invent a classification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Canonical industry buckets (Arabic + English synonyms).
_INDUSTRY_MAP: list[tuple[str, set[str]]] = [
    ("CONSTRUCTION", {
        "construction", "building", "contractor", "مقاولات", "بناء", "تشييد",
        "civil engineering", "real estate development", "تطوير عقاري",
    }),
    ("REAL_ESTATE", {
        "real estate", "property", "عقار", "عقارات", "property management",
        "تمليك", "تأجير",
    }),
    ("RETAIL", {
        "retail", "wholesale", "trading", "تجارة", "بقالة", "سوبر ماركت",
        "supermarket", "hypermarket", "distribution", "توزيع", "استيراد",
        "import", "export", "تصدير",
    }),
    ("HEALTHCARE", {
        "healthcare", "medical", "hospital", "pharmacy", "رعاية صحية", "مستشفى",
        "صيدلية", "عيادة", "clinic", "pharmaceutical", "دواء",
    }),
    ("FINANCIAL_SERVICES", {
        "financial", "bank", "insurance", "investment", "تأمين", "بنك", "استثمار",
        "money exchange", "تحويل", "صيرفة", "fintech",
    }),
    ("FOOD_BEVERAGE", {
        "food", "restaurant", "café", "cafe", "bakery", "مطعم", "مقهى",
        "مخابز", "agro", "agriculture", "زراعة", "dairy", "ألبان", "meat", "لحوم",
    }),
    ("MANUFACTURING", {
        "manufacturing", "factory", "industrial", "صناعة", "مصنع", "تصنيع",
        "fabrication", "الحديد", "الخشب", "plastic", "بلاستيك", "steel",
        "aluminum", "ألمنيوم",
    }),
    ("ICT_TECHNOLOGY", {
        "technology", "software", "information technology", "it ", "telecom",
        "telecommunications", "تقنية", "برمجيات", "اتصالات", "cyber", "data",
        "digital", "computer", "حاسوب",
    }),
    ("LOGISTICS_TRANSPORT", {
        "logistics", "transport", "shipping", "freight", "نقل", "شحن", "لوجستي",
        "delivery", "توصيل", "trucking", "cars", "سيارات", "automotive",
    }),
    ("EDUCATION", {
        "education", "school", "university", "training", "تعليم", "مدرسة",
        "جامعة", "تدريب", "academy", "أكاديمية",
    }),
    ("HOSPITALITY", {
        "hotel", "hospitality", "tourism", "travel", "فندق", "سياحة", "سفر",
        "فندقية",
    }),
    ("ENERGY", {
        "energy", "oil", "gas", "electricity", "power", "petroleum", "طاقة",
        "نفط", "غاز", "كهرباء", "petrol", "وقود", "خدمات بترولية",
    }),
    ("PROFESSIONAL_SERVICES", {
        "consulting", "legal", "accounting", "audit", "استشارات", "قانونية",
        "محاسبة", "تدقيق", "management", "hr", "موارد بشرية", "recruitment",
        "توظيف",
    }),
]

# Normalization → strip stray punctuation, collapse space, lowercase.
_CLEAN_RE = re.compile(r"[^\w\s\u0600-\u06FF-]+")


def clean_industry(raw: str | None) -> str:
    if not raw:
        return ""
    s = raw.strip().lower()
    s = _CLEAN_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class IndustryResult:
    raw_industry: str
    normalized_industry: str
    industry_code: str | None
    normalization_method: str  # MAPPED / CLEANED


def normalize_industry(raw: str | None) -> IndustryResult:
    """Normalize a raw industry string to a canonical bucket + code.

    - raw is never modified.
    - MAPPED when a canonical bucket matches; code = short bucket code.
    - CLEANED otherwise (normalized == cleaned raw, code == None). We do NOT
      fabricate a bucket for unmatched text.
    """
    if not raw:
        return IndustryResult("", "", None, "CLEANED")
    raw_s = str(raw).strip()
    cleaned = clean_industry(raw_s)
    if not cleaned:
        return IndustryResult(raw_s, "", None, "CLEANED")

    norm = cleaned
    code = None
    method = "CLEANED"
    for label, keys in _INDUSTRY_MAP:
        for k in keys:
            if k in ("it ",) and k not in (" " + norm + " "):
                # 'it ' requires word-boundary match to avoid 'in'/'bit' etc.
                if k.strip() not in re.split(r"\s+", norm):
                    continue
            if k in norm or k.lstrip(" ") in (" " + norm) or k.rstrip(" ") in (norm + " "):
                if k.strip() and (k.strip() in norm.split(" ") or k.strip() in norm):
                    norm = label
                    code = label
                    method = "MAPPED"
                    break
        if method == "MAPPED":
            break

    return IndustryResult(raw_s, norm, code, method)
