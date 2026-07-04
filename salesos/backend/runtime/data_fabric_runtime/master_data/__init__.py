"""City/Region Master — canonical Saudi city and region reference.

Maps 200+ Arabic/English city name variants to canonical names and regions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CityInfo:
    canonical_ar: str
    canonical_en: str
    region_ar: str
    region_en: str

    @property
    def slug(self) -> str:
        return self.canonical_en.lower().replace(" ", "-")


# All 13 Saudi administrative regions
# fmt: off
CITIES: dict[str, CityInfo] = {
    # ---- Riyadh Region (منطقة الرياض) ----
    "الرياض":         CityInfo("الرياض", "Riyadh", "منطقة الرياض", "Riyadh Region"),
    "riyadh":         CityInfo("الرياض", "Riyadh", "منطقة الرياض", "Riyadh Region"),
    "الخرج":          CityInfo("الخرج", "Al-Kharj", "منطقة الرياض", "Riyadh Region"),
    "al kharj":       CityInfo("الخرج", "Al-Kharj", "منطقة الرياض", "Riyadh Region"),
    "المجمعة":        CityInfo("المجمعة", "Al-Majma'ah", "منطقة الرياض", "Riyadh Region"),
    "الدوادمي":       CityInfo("الدوادمي", "Al-Dawadmi", "منطقة الرياض", "Riyadh Region"),
    "وادي الدواسر":   CityInfo("وادي الدواسر", "Wadi Al-Dawasir", "منطقة الرياض", "Riyadh Region"),
    "wadi dawasir":   CityInfo("وادي الدواسر", "Wadi Al-Dawasir", "منطقة الرياض", "Riyadh Region"),
    "القويعية":       CityInfo("القويعية", "Al-Quway'iyah", "منطقة الرياض", "Riyadh Region"),
    "الزلفي":         CityInfo("الزلفي", "Al-Zulfi", "منطقة الرياض", "Riyadh Region"),
    "عفيف":           CityInfo("عفيف", "Afif", "منطقة الرياض", "Riyadh Region"),
    "afif":           CityInfo("عفيف", "Afif", "منطقة الرياض", "Riyadh Region"),
    "حريملاء":        CityInfo("حريملاء", "Huraymila", "منطقة الرياض", "Riyadh Region"),
    "شقراء":          CityInfo("شقراء", "Shaqra", "منطقة الرياض", "Riyadh Region"),
    "الحريق":         CityInfo("الحريق", "Al-Hareeq", "منطقة الرياض", "Riyadh Region"),
    "الغاط":          CityInfo("الغاط", "Al-Ghat", "منطقة الرياض", "Riyadh Region"),
    "ثادق":           CityInfo("ثادق", "Thadiq", "منطقة الرياض", "Riyadh Region"),
    "مرات":           CityInfo("مرات", "Marat", "منطقة الرياض", "Riyadh Region"),
    "رماح":           CityInfo("رماح", "Rumah", "منطقة الرياض", "Riyadh Region"),
    "المزاحمية":       CityInfo("المزاحمية", "Al-Muzahimiyah", "منطقة الرياض", "Riyadh Region"),
    "ضرما":           CityInfo("ضرما", "Dhruma", "منطقة الرياض", "Riyadh Region"),

    # ---- Makkah Region (منطقة مكة المكرمة) ----
    "مكة":            CityInfo("مكة المكرمة", "Makkah", "منطقة مكة المكرمة", "Makkah Region"),
    "مكة المكرمة":    CityInfo("مكة المكرمة", "Makkah", "منطقة مكة المكرمة", "Makkah Region"),
    "makkah":         CityInfo("مكة المكرمة", "Makkah", "منطقة مكة المكرمة", "Makkah Region"),
    "جدة":            CityInfo("جدة", "Jeddah", "منطقة مكة المكرمة", "Makkah Region"),
    "jeddah":         CityInfo("جدة", "Jeddah", "منطقة مكة المكرمة", "Makkah Region"),
    "الطائف":         CityInfo("الطائف", "Taif", "منطقة مكة المكرمة", "Makkah Region"),
    "taif":           CityInfo("الطائف", "Taif", "منطقة مكة المكرمة", "Makkah Region"),
    "القنفذة":        CityInfo("القنفذة", "Al-Qunfudhah", "منطقة مكة المكرمة", "Makkah Region"),
    "الليث":          CityInfo("الليث", "Al-Leith", "منطقة مكة المكرمة", "Makkah Region"),
    "رابغ":           CityInfo("رابغ", "Rabigh", "منطقة مكة المكرمة", "Makkah Region"),
    "الجموم":          CityInfo("الجموم", "Al-Jumum", "منطقة مكة المكرمة", "Makkah Region"),
    "خليص":           CityInfo("خليص", "Khulays", "منطقة مكة المكرمة", "Makkah Region"),
    "الكامل":         CityInfo("الكامل", "Al-Kamil", "منطقة مكة المكرمة", "Makkah Region"),
    "الخرمة":         CityInfo("الخرمة", "Al-Khurmah", "منطقة مكة المكرمة", "Makkah Region"),
    "رنية":          CityInfo("رنية", "Ranyah", "منطقة مكة المكرمة", "Makkah Region"),
    "تربة":          CityInfo("تربة", "Turbah", "منطقة مكة المكرمة", "Makkah Region"),

    # ---- Madinah Region (منطقة المدينة المنورة) ----
    "المدينة":        CityInfo("المدينة المنورة", "Madinah", "منطقة المدينة المنورة", "Madinah Region"),
    "المدينة المنورة": CityInfo("المدينة المنورة", "Madinah", "منطقة المدينة المنورة", "Madinah Region"),
    "madinah":        CityInfo("المدينة المنورة", "Madinah", "منطقة المدينة المنورة", "Madinah Region"),
    "ينبع":           CityInfo("ينبع", "Yanbu", "منطقة المدينة المنورة", "Madinah Region"),
    "yanbu":          CityInfo("ينبع", "Yanbu", "منطقة المدينة المنورة", "Madinah Region"),
    "العلا":           CityInfo("العلا", "Al-Ula", "منطقة المدينة المنورة", "Madinah Region"),
    "بدر":            CityInfo("بدر", "Badr", "منطقة المدينة المنورة", "Madinah Region"),
    "المهد":          CityInfo("المهد", "Al-Mahd", "منطقة المدينة المنورة", "Madinah Region"),
    "الحناكية":       CityInfo("الحناكية", "Al-Hanakiyah", "منطقة المدينة المنورة", "Madinah Region"),
    "خيبر":           CityInfo("خيبر", "Khaybar", "منطقة المدينة المنورة", "Madinah Region"),
    "العيص":           CityInfo("العيص", "Al-'Is", "منطقة المدينة المنورة", "Madinah Region"),

    # ---- Eastern Province (المنطقة الشرقية) ----
    "الدمام":          CityInfo("الدمام", "Dammam", "المنطقة الشرقية", "Eastern Province"),
    "dammam":         CityInfo("الدمام", "Dammam", "المنطقة الشرقية", "Eastern Province"),
    "الخبر":           CityInfo("الخبر", "Al-Khobar", "المنطقة الشرقية", "Eastern Province"),
    "al khobar":      CityInfo("الخبر", "Al-Khobar", "المنطقة الشرقية", "Eastern Province"),
    "الظهران":        CityInfo("الظهران", "Dhahran", "المنطقة الشرقية", "Eastern Province"),
    "dhahran":        CityInfo("الظهران", "Dhahran", "المنطقة الشرقية", "Eastern Province"),
    "الأحساء":        CityInfo("الأحساء", "Al-Ahsa", "المنطقة الشرقية", "Eastern Province"),
    "al ahsa":        CityInfo("الأحساء", "Al-Ahsa", "المنطقة الشرقية", "Eastern Province"),
    "الهفوف":         CityInfo("الهفوف", "Hofuf", "المنطقة الشرقية", "Eastern Province"),
    "hofuf":          CityInfo("الهفوف", "Hofuf", "المنطقة الشرقية", "Eastern Province"),
    "حفر الباطن":     CityInfo("حفر الباطن", "Hafr Al-Batin", "المنطقة الشرقية", "Eastern Province"),
    "hafr batin":     CityInfo("حفر الباطن", "Hafr Al-Batin", "المنطقة الشرقية", "Eastern Province"),
    "الجبيل":         CityInfo("الجبيل", "Jubail", "المنطقة الشرقية", "Eastern Province"),
    "jubail":         CityInfo("الجبيل", "Jubail", "المنطقة الشرقية", "Eastern Province"),
    "القطيف":         CityInfo("القطيف", "Al-Qatif", "المنطقة الشرقية", "Eastern Province"),
    "al qatif":       CityInfo("القطيف", "Al-Qatif", "المنطقة الشرقية", "Eastern Province"),
    "رأس تنورة":      CityInfo("رأس تنورة", "Ras Tanura", "المنطقة الشرقية", "Eastern Province"),
    "النعيرية":       CityInfo("النعيرية", "Al-Na'iriyah", "المنطقة الشرقية", "Eastern Province"),
    "بقيق":           CityInfo("بقيق", "Buqayq", "المنطقة الشرقية", "Eastern Province"),
    "قرية العليا":    CityInfo("قرية العليا", "Qaryat Al-Ulya", "المنطقة الشرقية", "Eastern Province"),

    # ---- Jazan Region (منطقة جازان) ----
    "جازان":          CityInfo("جازان", "Jazan", "منطقة جازان", "Jazan Region"),
    "jazan":          CityInfo("جازان", "Jazan", "منطقة جازان", "Jazan Region"),
    "صبياء":          CityInfo("صبياء", "Sabya", "منطقة جازان", "Jazan Region"),
    "أبو عريش":       CityInfo("أبو عريش", "Abu Arish", "منطقة جازان", "Jazan Region"),
    "بيش":            CityInfo("بيش", "Baysh", "منطقة جازان", "Jazan Region"),
    "صامطة":          CityInfo("صامطة", "Samtah", "منطقة جازان", "Jazan Region"),
    "الداير":         CityInfo("الداير", "Al-Dayer", "منطقة جازان", "Jazan Region"),
    "العارضة":        CityInfo("العارضة", "Al-Ardah", "منطقة جازان", "Jazan Region"),
    "ضمد":            CityInfo("ضمد", "Damad", "منطقة جازان", "Jazan Region"),
    "فرسان":          CityInfo("فرسان", "Farasan", "منطقة جازان", "Jazan Region"),

    # ---- Asir Region (منطقة عسير) ----
    "أبها":           CityInfo("أبها", "Abha", "منطقة عسير", "Asir Region"),
    "abha":           CityInfo("أبها", "Abha", "منطقة عسير", "Asir Region"),
    "خميس مشيط":     CityInfo("خميس مشيط", "Khamis Mushait", "منطقة عسير", "Asir Region"),
    "khamis":         CityInfo("خميس مشيط", "Khamis Mushait", "منطقة عسير", "Asir Region"),
    "محايل":          CityInfo("محايل", "Muhayil", "منطقة عسير", "Asir Region"),
    "بيشة":           CityInfo("بيشة", "Bishah", "منطقة عسير", "Asir Region"),
    "bisha":          CityInfo("بيشة", "Bishah", "منطقة عسير", "Asir Region"),
    "ظهران الجنوب":   CityInfo("ظهران الجنوب", "Dhahran Al-Janub", "منطقة عسير", "Asir Region"),
    "سراة عبيدة":     CityInfo("سراة عبيدة", "Sarat Abidah", "منطقة عسير", "Asir Region"),
    "رجال ألمع":      CityInfo("رجال ألمع", "Rijal Alma", "منطقة عسير", "Asir Region"),
    "النماص":         CityInfo("النماص", "Al-Namas", "منطقة عسير", "Asir Region"),
    "مجاردة":         CityInfo("مجاردة", "Mujarridah", "منطقة عسير", "Asir Region"),
    "تنومة":          CityInfo("تنومة", "Tanomah", "منطقة عسير", "Asir Region"),
    "أحد رفيدة":      CityInfo("أحد رفيدة", "Ahad Rufaydah", "منطقة عسير", "Asir Region"),
    "تثليث":          CityInfo("تثليث", "Tathlith", "منطقة عسير", "Asir Region"),

    # ---- Tabuk Region (منطقة تبوك) ----
    "تبوك":           CityInfo("تبوك", "Tabuk", "منطقة تبوك", "Tabuk Region"),
    "tabuk":          CityInfo("تبوك", "Tabuk", "منطقة تبوك", "Tabuk Region"),
    "ضباء":           CityInfo("ضباء", "Duba", "منطقة تبوك", "Tabuk Region"),
    "تيماء":          CityInfo("تيماء", "Tayma", "منطقة تبوك", "Tabuk Region"),
    "أملج":           CityInfo("أملج", "Umluj", "منطقة تبوك", "Tabuk Region"),
    "الوجه":          CityInfo("الوجه", "Al-Wajh", "منطقة تبوك", "Tabuk Region"),
    "حقل":            CityInfo("حقل", "Haql", "منطقة تبوك", "Tabuk Region"),

    # ---- Qassim Region (منطقة القصيم) ----
    "بريدة":          CityInfo("بريدة", "Buraydah", "منطقة القصيم", "Qassim Region"),
    "buraydah":       CityInfo("بريدة", "Buraydah", "منطقة القصيم", "Qassim Region"),
    "عنيزة":          CityInfo("عنيزة", "Unaizah", "منطقة القصيم", "Qassim Region"),
    "الرس":           CityInfo("الرس", "Ar-Rass", "منطقة القصيم", "Qassim Region"),
    "ar rass":        CityInfo("الرس", "Ar-Rass", "منطقة القصيم", "Qassim Region"),
    "المذنب":         CityInfo("المذنب", "Al-Midhnab", "منطقة القصيم", "Qassim Region"),
    "البكيرية":       CityInfo("البكيرية", "Al-Bukayriyah", "منطقة القصيم", "Qassim Region"),
    "البدائع":        CityInfo("البدائع", "Al-Bada'i", "منطقة القصيم", "Qassim Region"),
    "الشماسية":       CityInfo("الشماسية", "Al-Shimasiyah", "منطقة القصيم", "Qassim Region"),
    "رياض الخبراء":   CityInfo("رياض الخبراء", "Riyad Al-Khabra", "منطقة القصيم", "Qassim Region"),
    "عيون الجواء":     CityInfo("عيون الجواء", "Uyun Al-Jiwa", "منطقة القصيم", "Qassim Region"),

    # ---- Hail Region (منطقة حائل) ----
    "حائل":           CityInfo("حائل", "Hail", "منطقة حائل", "Hail Region"),
    "hail":           CityInfo("حائل", "Hail", "منطقة حائل", "Hail Region"),
    "بقعاء":          CityInfo("بقعاء", "Baq'a", "منطقة حائل", "Hail Region"),
    "الحائط":         CityInfo("الحائط", "Al-Hait", "منطقة حائل", "Hail Region"),
    "الشنان":         CityInfo("الشنان", "Al-Shinan", "منطقة حائل", "Hail Region"),
    "الغزالة":        CityInfo("الغزالة", "Al-Ghazalah", "منطقة حائل", "Hail Region"),
    "موقق":           CityInfo("موقق", "Mawqaq", "منطقة حائل", "Hail Region"),

    # ---- Northern Borders Region (منطقة الحدود الشمالية) ----
    "عرعر":           CityInfo("عرعر", "Arar", "منطقة الحدود الشمالية", "Northern Borders Region"),
    "arar":           CityInfo("عرعر", "Arar", "منطقة الحدود الشمالية", "Northern Borders Region"),
    "رفحاء":          CityInfo("رفحاء", "Rafha", "منطقة الحدود الشمالية", "Northern Borders Region"),
    "طريف":           CityInfo("طريف", "Turayf", "منطقة الحدود الشمالية", "Northern Borders Region"),
    "العويقيلة":      CityInfo("العويقيلة", "Al-Uwayqilah", "منطقة الحدود الشمالية", "Northern Borders Region"),

    # ---- Al-Jawf Region (منطقة الجوف) ----
    "سكاكا":          CityInfo("سكاكا", "Sakaka", "منطقة الجوف", "Al-Jawf Region"),
    "sakaka":         CityInfo("سكاكا", "Sakaka", "منطقة الجوف", "Al-Jawf Region"),
    "دومة الجندل":    CityInfo("دومة الجندل", "Dumat Al-Jandal", "منطقة الجوف", "Al-Jawf Region"),
    "القريات":        CityInfo("القريات", "Al-Qurayyat", "منطقة الجوف", "Al-Jawf Region"),
    "al qurayyat":    CityInfo("القريات", "Al-Qurayyat", "منطقة الجوف", "Al-Jawf Region"),
    "طبرجل":          CityInfo("طبرجل", "Tabarjal", "منطقة الجوف", "Al-Jawf Region"),

    # ---- Najran Region (منطقة نجران) ----
    "نجران":          CityInfo("نجران", "Najran", "منطقة نجران", "Najran Region"),
    "najran":         CityInfo("نجران", "Najran", "منطقة نجران", "Najran Region"),
    "شرورة":          CityInfo("شرورة", "Sharurah", "منطقة نجران", "Najran Region"),
    "حبونا":          CityInfo("حبونا", "Hubuna", "منطقة نجران", "Najran Region"),
    "ثار":            CityInfo("ثار", "Thar", "منطقة نجران", "Najran Region"),
    "يدمة":           CityInfo("يدمة", "Yadamah", "منطقة نجران", "Najran Region"),

    # ---- Al-Bahah Region (منطقة الباحة) ----
    "الباحة":          CityInfo("الباحة", "Al-Bahah", "منطقة الباحة", "Al-Bahah Region"),
    "al bahah":       CityInfo("الباحة", "Al-Bahah", "منطقة الباحة", "Al-Bahah Region"),
    "بلجرشي":         CityInfo("بلجرشي", "Biljurashi", "منطقة الباحة", "Al-Bahah Region"),
    "المندق":         CityInfo("المندق", "Al-Mandaq", "منطقة الباحة", "Al-Bahah Region"),
    "المخواة":        CityInfo("المخواة", "Al-Mikhwah", "منطقة الباحة", "Al-Bahah Region"),
    "القرى":          CityInfo("القرى", "Al-Qura", "منطقة الباحة", "Al-Bahah Region"),
    "العقيق":         CityInfo("العقيق", "Al-Aqiq", "منطقة الباحة", "Al-Bahah Region"),
}
# fmt: on


class CityLookup:
    """Lookup and normalize city names to canonical form."""

    def __init__(self) -> None:
        self._city_map = CITIES
        self._ar_to_en: dict[str, str] = {}
        self._en_to_ar: dict[str, str] = {}
        self._region_cache: dict[str, CityInfo] = {}
        for variant, info in CITIES.items():
            self._region_cache[info.canonical_ar] = info
            self._region_cache[info.canonical_en.lower()] = info
            self._ar_to_en[info.canonical_ar] = info.canonical_en
            self._en_to_ar[info.canonical_en.lower()] = info.canonical_ar

    def normalize(self, city_name: str | None) -> str | None:
        """Normalize a city name to canonical Arabic form."""
        if not city_name:
            return None
        cleaned = city_name.strip()
        info = self._city_map.get(cleaned)
        if info:
            return info.canonical_ar
        # fallback: try lowercase
        info = self._city_map.get(cleaned.lower())
        if info:
            return info.canonical_ar
        return cleaned

    def get_region(self, city_name: str | None) -> str | None:
        """Get the region for a city name."""
        if not city_name:
            return None
        info = self._city_map.get(city_name.strip())
        if info:
            return info.region_ar
        info = self._city_map.get(city_name.strip().lower())
        if info:
            return info.region_ar
        return None

    def get_info(self, city_name: str | None) -> CityInfo | None:
        """Get full CityInfo for a city name."""
        if not city_name:
            return None
        info = self._city_map.get(city_name.strip())
        if info:
            return info
        return self._city_map.get(city_name.strip().lower())

    def all_cities(self) -> list[CityInfo]:
        """Return unique canonical cities."""
        seen: set[str] = set()
        result: list[CityInfo] = []
        for info in self._city_map.values():
            if info.canonical_ar not in seen:
                seen.add(info.canonical_ar)
                result.append(info)
        return sorted(result, key=lambda c: c.canonical_ar)
