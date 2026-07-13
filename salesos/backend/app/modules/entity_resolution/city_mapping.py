"""Saudi City & Region Normalization — mappings for entity resolution.

Normalizes city and region names across different Arabic/English spellings
and variants commonly found in Saudi government data sources.

Sources exhibit inconsistent naming:
- "الرياض", "الرياض منطقة", "Riyadh", "رياض", "Ar Riyad"
- "جدة", "جده", "Jeddah", "Jedda", "Jiddah"
- "مكة المكرمة", "مكه المكرمه", "مكة", "Makkah", "Mecca"
"""

from __future__ import annotations

from typing import ClassVar


class CityRegionNormalizer:
    """Normalizes Saudi city and region names to canonical forms.

    Maps variants (Arabic, English, abbreviations) to a canonical Arabic name
    and a canonical English name.

    Usage:
        normalizer = CityRegionNormalizer()
        canonical = normalizer.normalize_city("جده")  # → "جدة"
        english = normalizer.to_english("الرياض")      # → "Riyadh"
    """

    # Maps every variant → canonical Arabic name
    _CITY_MAP: ClassVar[dict[str, str]] = {
        # ── Riyadh / الرياض ──
        "الرياض": "الرياض",
        "رياض": "الرياض",
        "الرياض منطقة": "الرياض",
        "منطقة الرياض": "الرياض",
        "riyadh": "الرياض",
        "riyaadh": "الرياض",
        "ar riyad": "الرياض",
        "ar-riyad": "الرياض",

        # ── Jeddah / جدة ──
        "جدة": "جدة",
        "جده": "جدة",
        "جدا": "جدة",
        "jeddah": "جدة",
        "jedda": "جدة",
        "jiddah": "جدة",
        "jeddah city": "جدة",

        # ── Dammam / الدمام ──
        "الدمام": "الدمام",
        "دمام": "الدمام",
        "dammam": "الدمام",
        "damam": "الدمام",
        "ad dammam": "الدمام",

        # ── Makkah / مكة المكرمة ──
        "مكة المكرمة": "مكة المكرمة",
        "مكه المكرمه": "مكة المكرمة",
        "مكة": "مكة المكرمة",
        "مكه": "مكة المكرمة",
        "makkah": "مكة المكرمة",
        "mecca": "مكة المكرمة",
        "makka": "مكة المكرمة",
        "makkah al mukarramah": "مكة المكرمة",

        # ── Madinah / المدينة المنورة ──
        "المدينة المنورة": "المدينة المنورة",
        "المدينه المنوره": "المدينة المنورة",
        "المدينة": "المدينة المنورة",
        "المدينه": "المدينة المنورة",
        "طيبة": "المدينة المنورة",
        "madina": "المدينة المنورة",
        "medina": "المدينة المنورة",
        "al madinah": "المدينة المنورة",

        # ── Khobar / الخبر ──
        "الخبر": "الخبر",
        "خبر": "الخبر",
        "khobar": "الخبر",
        "al khobar": "الخبر",
        "al khubar": "الخبر",

        # ── Dhahran / الظهران ──
        "الظهران": "الظهران",
        "ظهران": "الظهران",
        "dhahran": "الظهران",
        "zahran": "الظهران",

        # ── Jubail / الجبيل ──
        "الجبيل": "الجبيل",
        "جبيل": "الجبيل",
        "مدينة الجبيل الصناعية": "الجبيل",
        "jubail": "الجبيل",
        "al jubail": "الجبيل",
        "jubail industrial city": "الجبيل",

        # ── Yanbu / ينبع ──
        "ينبع": "ينبع",
        "ينبع الصناعية": "ينبع",
        "yanbu": "ينبع",
        "yanbu industrial": "ينبع",

        # ── Taif / الطائف ──
        "الطائف": "الطائف",
        "طائف": "الطائف",
        "taif": "الطائف",
        "at taif": "الطائف",

        # ── Tabuk / تبوك ──
        "تبوك": "تبوك",
        "tabuk": "تبوك",
        "tabouk": "تبوك",

        # ── Buraidah / بريدة ──
        "بريدة": "بريدة",
        "بريده": "بريدة",
        "buraidah": "بريدة",
        "buraydah": "بريدة",

        # ── Abha / أبها ──
        "أبها": "أبها",
        "ابها": "أبها",
        "abha": "أبها",

        # ── Hail / حائل ──
        "حائل": "حائل",
        "hail": "حائل",
        "ha'il": "حائل",

        # ── Jizan / جازان ──
        "جازان": "جازان",
        "جيزان": "جازان",
        "jazan": "جازان",
        "jizan": "جازان",
        "gizan": "جازان",

        # ── Najran / نجران ──
        "نجران": "نجران",
        "najran": "نجران",

        # ── Al-Ahsa / الأحساء ──
        "الأحساء": "الأحساء",
        "الاحساء": "الأحساء",
        "حسا": "الأحساء",
        "الهفوف": "الأحساء",
        "ahsa": "الأحساء",
        "al ahsa": "الأحساء",
        "hassa": "الأحساء",
        "hofuf": "الأحساء",

        # ── Al-Kharj / الخرج ──
        "الخرج": "الخرج",
        "خرج": "الخرج",
        "سيح": "الخرج",
        "kharj": "الخرج",
        "al kharj": "الخرج",

        # ── Al-Qassim / القصيم ──
        "القصيم": "القصيم",
        "منطقة القصيم": "القصيم",
        "qassim": "القصيم",
        "al qassim": "القصيم",
        "gassim": "القصيم",

        # ── Northern Borders / الحدود الشمالية ──
        "الحدود الشمالية": "الحدود الشمالية",
        "الحدود الشماليه": "الحدود الشمالية",
        "عرعر": "الحدود الشمالية",
        "arar": "الحدود الشمالية",

        # ── Al-Jawf / الجوف ──
        "الجوف": "الجوف",
        "سكاكا": "الجوف",
        "jouf": "الجوف",
        "al jouf": "الجوف",

        # ── Al-Baha / الباحة ──
        "الباحة": "الباحة",
        "الباحه": "الباحة",
        "baha": "الباحة",
        "al baha": "الباحة",

        # ── Asir / عسير ──
        "عسير": "عسير",
        "منطقة عسير": "عسير",
        "asir": "عسير",
        "aseer": "عسير",
        "abha": "أبها",

        # ── Eastern Province / الشرقية ──
        "المنطقة الشرقية": "المنطقة الشرقية",
        "المنطقه الشرقيه": "المنطقة الشرقية",
        "الشرقية": "المنطقة الشرقية",
        "الشرقيه": "المنطقة الشرقية",
        "eastern province": "المنطقة الشرقية",
        "sharqiya": "المنطقة الشرقية",
        "ash sharqiyah": "المنطقة الشرقية",
    }

    # Canonical Arabic → English
    _CITY_TO_ENGLISH: ClassVar[dict[str, str]] = {
        "الرياض": "Riyadh",
        "جدة": "Jeddah",
        "الدمام": "Dammam",
        "مكة المكرمة": "Makkah",
        "المدينة المنورة": "Madinah",
        "الخبر": "Khobar",
        "الظهران": "Dhahran",
        "الجبيل": "Jubail",
        "ينبع": "Yanbu",
        "الطائف": "Taif",
        "تبوك": "Tabuk",
        "بريدة": "Buraidah",
        "أبها": "Abha",
        "حائل": "Hail",
        "جازان": "Jazan",
        "نجران": "Najran",
        "الأحساء": "Al-Ahsa",
        "الخرج": "Al-Kharj",
        "القصيم": "Al-Qassim",
        "الحدود الشمالية": "Northern Borders",
        "الجوف": "Al-Jawf",
        "الباحة": "Al-Baha",
        "عسير": "Asir",
        "المنطقة الشرقية": "Eastern Province",
    }

    def normalize_city(self, city: str) -> str:
        """Normalize a city name to its canonical Arabic form.

        Args:
            city: Raw city name in Arabic or English

        Returns:
            Canonical Arabic city name, or original if unknown
        """
        if not city:
            return ""
        cleaned = city.strip()
        return self._CITY_MAP.get(cleaned, self._CITY_MAP.get(cleaned.lower(), cleaned))

    def normalize_region(self, region: str) -> str:
        """Normalize a region name to its canonical Arabic form."""
        return self.normalize_city(region)

    def to_english(self, city_ar: str) -> str:
        """Convert a canonical Arabic city name to English.

        Args:
            city_ar: Canonical Arabic city name

        Returns:
            English name, or original if unknown
        """
        if not city_ar:
            return ""
        return self._CITY_TO_ENGLISH.get(city_ar, city_ar)

    def normalize_and_english(self, city: str) -> tuple[str, str]:
        """Normalize and return both Arabic canonical and English form.

        Returns:
            Tuple of (canonical_arabic, english_name)
        """
        ar = self.normalize_city(city)
        en = self.to_english(ar)
        return (ar, en)

    @staticmethod
    def default() -> CityRegionNormalizer:
        return CityRegionNormalizer()
