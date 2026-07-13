"""Arabic Search Thesaurus — business term synonyms for query expansion.

Used to expand search queries with semantically equivalent terms to improve
recall for Arabic business searches.

Example:
    Query: "مقاولات" → expands to include "إنشاءات", "تشييد", "بناء"
    Query: "شركة" → expands to include "مؤسسة", "منشأة", "مصنع"
"""

from __future__ import annotations

from typing import ClassVar


class ArabicSearchThesaurus:
    """Business-domain thesaurus for Arabic search query expansion.

    Maps common business terms to their synonyms, abbreviations,
    and alternative spellings. Used by the search pipeline to
    broaden queries and improve recall.

    Usage:
        thesaurus = ArabicSearchThesaurus()
        expanded = thesaurus.expand("مقاولات")
        # → ["مقاولات", "إنشاءات", "تشييد", "بناء", "تعمير"]
    """

    # ── Company Types ──────────────────────────────────────────────────

    _COMPANY_TYPES: ClassVar[dict[str, list[str]]] = {
        "شركة": ["مؤسسة", "منشأة", "مصنع", "شركه"],
        "مؤسسة": ["شركة", "منشأة"],
        "مصنع": ["شركة", "منشأة", "معمل", "ورشة"],
        "مكتب": ["مكتب", "فرع"],
        "مجموعة": ["شركة", "تكتل", "تحالف"],
        "منشأة": ["شركة", "مؤسسة", "مصنع"],
    }

    # ── Industries / Sectors ────────────────────────────────────────────

    _INDUSTRIES: ClassVar[dict[str, list[str]]] = {
        "مقاولات": ["إنشاءات", "تشييد", "بناء", "تعمير", "مقاوله"],
        "تجارة": ["بيع", "شراء", "تسويق", "توزيع", "متاجره"],
        "صناعة": ["تصنيع", "إنتاج", "تحويل", "صناعه"],
        "زراعة": ["فلاحة", "حراثة", "زراعه"],
        "نقل": ["شحن", "توصيل", "لوجستيات", "مواصلات"],
        "تعليم": ["تدريب", "تطوير", "تربية", "تعليمي"],
        "صحة": ["طبي", "مستشفى", "عيادة", "علاج", "دواء"],
        "تقنية": ["تكنولوجيا", "برمجيات", "حاسب", "إلكتروني", "رقمي", "تقنيه"],
        "عقارات": ["عقار", "أراضي", "إسكان", "تطوير عقاري", "عقاريه"],
        "تمويل": ["بنوك", "مصارف", "استثمار", "تأمين", "قروض"],
        "اتصالات": ["جوال", "هاتف", "إنترنت", "شبكات"],
        "طاقة": ["بترول", "غاز", "كهرباء", "متجددة", "شمسي"],
        "سياحة": ["فندقة", "سفر", "ترفيه", "ضيافة"],
        "إعلام": ["نشر", "طباعة", "دعاية", "صحافة", "تلفزيون"],
        "غذاء": ["أغذية", "مطاعم", "تموين", "مشروبات"],
        "استشارات": ["استشاريه", "خبراء", "مستشارين", "دراسات"],
        "هندسة": ["هندسي", "تصميم", "تخطيط", "معماري"],
        "قانون": ["محاماة", "استشارات قانونية", "محامين", "تحكيم"],
        "مياه": ["تحليه", "صرف صحي", "ري"],
        "تعدين": ["مناجم", "معادن", "تعدينيه"],
    }

    # ── Business Terms ──────────────────────────────────────────────────

    _BUSINESS_TERMS: ClassVar[dict[str, list[str]]] = {
        "عقود": ["عقد", "اتفاقيات", "اتفاقيه", "تعاقد"],
        "مناقصات": ["مناقصه", "عطاءات", "ترسيه", "ترسية"],
        "مشاريع": ["مشروع", "مشاريع", "أعمال"],
        "خدمات": ["خدمه", "حلول", "تعهيد", "إسناد"],
        "استيراد": ["استيراد", "توريد", "جلب", "شراء خارجي"],
        "تصدير": ["تصدير", "تسويق خارجي", "بيع خارجي"],
        "صيانة": ["صيانه", "إصلاح", "ترميم", "تشغيل"],
        "نظافة": ["نظافه", "تنظيف", "تطهير", "تعقيم"],
        "أمن": ["حماية", "حراسة", "سلامة", "مراقبة"],
        "تأجير": ["تأجير", "إيجار", "استئجار", "تأجير تمويلي"],
        "تطوير": ["تطوير", "تحسين", "تحديث", "ارتقاء"],
        "إدارة": ["إداره", "تشغيل", "تنظيم", "قيادة"],
        "استثمار": ["استثمار", "تملك", "مساهمة", "محفظة"],
        "تمويل": ["تمويل", "قرض", "ائتمان", "تسهيلات"],
        "تأمين": ["تأمين", "ضمان", "حماية تأمينية", "تعويض"],
        "تشغيل": ["تشغيل", "إدارة", "توظيف", "عمالة"],
    }

    # ── Legal / Government Terms ────────────────────────────────────────

    _LEGAL_TERMS: ClassVar[dict[str, list[str]]] = {
        "سجل تجاري": ["سجل", "تجاري", "ترخيص"],
        "ترخيص": ["رخصة", "تصريح", "إجازة", "ترخيص"],
        "زكاة": ["ضريبة", "دخل", "زكاة"],
        "ضريبة": ["زكاة", "قيمة مضافة", "ضرائب"],
        "تأسيس": ["إنشاء", "تكوين", "افتتاح"],
        "تصفية": ["إغلاق", "حل", "شطب", "إنهاء"],
        "اندماج": ["دمج", "ضم", "شراء", "استحواذ"],
    }

    # ── Location / Geographic ───────────────────────────────────────────

    _LOCATION_TERMS: ClassVar[dict[str, list[str]]] = {
        "الرياض": ["الرياض", "رياض"],
        "جدة": ["جده", "جدة"],
        "الدمام": ["الدمام", "دمام"],
        "مكة": ["مكه", "مكة المكرمة", "مكه المكرمه"],
        "المدينة": ["المدينه", "المدينة المنورة", "المدينه المنوره", "طيبة"],
        "المنطقة الشرقية": ["الشرقيه", "شرقية", "منطقه شرقيه"],
        "القصيم": ["القصيم", "بريدة", "بريده", "عنيزة"],
        "الخرج": ["الخرج", "سيح"],
        "الجبيل": ["الجبيل", "جبيل", "مدينة الجبيل الصناعية"],
    }

    # ── All terms combined ──────────────────────────────────────────────

    ALL_TERMS: ClassVar[dict[str, list[str]]] = {
        **_COMPANY_TYPES,
        **_INDUSTRIES,
        **_BUSINESS_TERMS,
        **_LEGAL_TERMS,
        **_LOCATION_TERMS,
    }

    def expand(self, term: str) -> list[str]:
        """Expand a single term to include its synonyms.

        Args:
            term: The search term to expand

        Returns:
            List containing the original term plus all known synonyms
        """
        term = term.strip()
        synonyms = self.ALL_TERMS.get(term, [])

        if not synonyms:
            # Try case-insensitive lookup for mixed languages
            term_lower = term.lower()
            for key, values in self.ALL_TERMS.items():
                if key.lower() == term_lower:
                    synonyms = values
                    break

        return [term] + [s for s in synonyms if s != term]

    def expand_query(self, query: str) -> str:
        """Expand a full query string by replacing terms with their synonyms.

        This performs simple word-by-word expansion. Each known term in the
        query is replaced with an OR group in PostgreSQL tsquery syntax.

        Args:
            query: The full search query text

        Returns:
            Expanded query string suitable for tsquery processing
        """
        tokens = query.split()
        expanded_tokens = []

        for token in tokens:
            synonyms = self.expand(token)
            if len(synonyms) > 1:
                # Create an OR group for PostgreSQL tsquery
                expanded_tokens.append("(" + " | ".join(synonyms) + ")")
            else:
                expanded_tokens.append(token)

        return " & ".join(expanded_tokens)

    def get_synonyms(self, term: str) -> list[str]:
        """Get synonyms for a term (without including the original)."""
        return self.expand(term)[1:]

    @staticmethod
    def default() -> ArabicSearchThesaurus:
        return ArabicSearchThesaurus()
