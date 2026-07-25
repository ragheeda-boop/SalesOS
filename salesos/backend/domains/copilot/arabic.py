"""Arabic copilot engine — NLP detection, RTL handling, Saudi business context.

Handles:
- Arabic input detection (Unicode range analysis)
- Arabic prompt templates for Saudi business context
- RTL text markers for correct rendering
- Saudi-specific references (CR, MOL, ZATCA, etc.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Arabic Unicode ranges
_ARABIC_RANGES = (
    (0x0600, 0x06FF),   # Arabic block
    (0x0750, 0x077F),   # Arabic Supplement
    (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
)

_ARABIC_RE = re.compile(
    "[" + "".join(f"\\u{lo:04x}-\\u{hi:04x}" for lo, hi in _ARABIC_RANGES) + "]"
)

_ARABIC_RATIO_THRESHOLD = 0.3


@dataclass
class ArabicDetectionResult:
    """Result of Arabic language detection."""

    is_arabic: bool = False
    arabic_ratio: float = 0.0
    contains_diacritics: bool = False
    detected_entities: list[str] = field(default_factory=list)


class ArabicCopilotEngine:
    """Arabic NLP pipeline for copilot responses."""

    # Saudi business entities patterns
    _CR_PATTERN = re.compile(
        r"(?:سجل\s*تجاري|cr|s\.c|سجل\s*ال thương|السجل\s*التجاري)"
        r"\s*[:\s]*(\d{10})", re.IGNORECASE,
    )
    _MOL_PATTERN = re.compile(
        r"(?:وزارة\s*العمل|موارد\s*البشرية|مكتب\s*العمل"
        r"|ministry\s*of\s*labor)\s*[:\s]*(\w+)", re.IGNORECASE,
    )
    _ZATCA_PATTERN = re.compile(
        r"(?:زاتكا|هيئة\s*الزكاة|zatca|الهيئة\s*الذهبية)"
        r"\s*[:\s]*(\w+)", re.IGNORECASE,
    )
    _VAT_PATTERN = re.compile(
        r"(?:ضريبة\s*القيمة\s*المضافة|vat|القيمة\s*المضافة)"
        r"\s*(\d{1,2})\s*%", re.IGNORECASE,
    )
    _CRUD_RE = re.compile(r"(?:cr|سجل\s*تجاري)\s*(\d{10})", re.IGNORECASE)

    # Saudi-specific terms
    SAUDI_CONTEXT_TERMS = {
        "رخصة_العمل": "Ministry of Human Resources and Social Development",
        "سجل_تجاري": "Commercial Registration (CR)",
        "ضريبة_القيمة_المضافة": "VAT — ZATCA",
        "هيئة_السعودية": "Saudi Authority for Industrial Cities",
        "الغرفة_التجارية": "Saudi Chambers of Commerce",
        "منصة_مدد": "Mudad — Saudi Labor Platform",
        "منصة_ embod": "Qiwa — Saudi Labor Platform",
        "الصرفة": "Saudi Central Bank (SAMA)",
        "الهيئة_الذهبية": "Saudi Arabian Monetary Authority",
        "الهيئة_السعودية_للقطاع_الخاص": "Saudi Arabian General Investment Authority",
    }

    def detect(self, text: str) -> ArabicDetectionResult:
        """Detect Arabic content in text."""
        if not text:
            return ArabicDetectionResult()

        arabic_chars = len(_ARABIC_RE.findall(text))
        total_chars = len(text.replace(" ", ""))
        ratio = arabic_chars / total_chars if total_chars > 0 else 0.0

        diacritics = bool(re.search(r"[\u064B-\u065F\u0670]", text))

        entities: list[str] = []
        if self._CR_PATTERN.search(text):
            entities.append("commercial_registration")
        if self._MOL_PATTERN.search(text):
            entities.append("ministry_of_labor")
        if self._ZATCA_PATTERN.search(text):
            entities.append("zatca")
        if self._VAT_PATTERN.search(text):
            entities.append("vat")

        return ArabicDetectionResult(
            is_arabic=ratio >= _ARABIC_RATIO_THRESHOLD,
            arabic_ratio=round(ratio, 3),
            contains_diacritics=diacritics,
            detected_entities=entities,
        )

    def detect_language(self, text: str) -> str:
        """Simple language detection returning 'ar' or 'en'."""
        result = self.detect(text)
        return "ar" if result.is_arabic else "en"

    def get_prompt_template(self, intent: str, language: str = "ar") -> str:
        """Get the appropriate prompt template for intent and language."""
        templates = _PROMPT_TEMPLATES if language == "ar" else _PROMPT_TEMPLATES_EN
        return templates.get(intent, templates.get("default", ""))

    def add_rtl_markers(self, text: str) -> str:
        """Add RTL Unicode markers for correct bidirectional rendering."""
        if not text:
            return text
        rtl_start = "\u202B"  # Right-to-Left Embedding
        rtl_end = "\u202C"    # Pop Directional Formatting
        ltr_marker = "\u202A" # Left-to-Right Embedding
        ltr_end = "\u202C"

        lines = text.split("\n")
        result_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result_lines.append(line)
                continue

            has_latin = bool(re.search(r"[a-zA-Z0-9]", stripped))
            has_arabic = bool(_ARABIC_RE.search(stripped))

            if has_arabic and has_latin:
                # Mixed content: wrap entire line in RTL, numbers in LTR
                processed = re.sub(
                    r"(\d[\d,.\-\/]*)",
                    f"{ltr_marker}\\1{ltr_end}",
                    stripped,
                )
                result_lines.append(f"{rtl_start}{processed}{rtl_end}")
            elif has_arabic:
                result_lines.append(f"{rtl_start}{stripped}{rtl_end}")
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    def enrich_saudi_context(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """Enrich context with Saudi-specific business information."""
        enriched = dict(context)

        cr_match = self._CRUD_RE.search(query)
        if cr_match:
            enriched["cr_number"] = cr_match.group(1)

        detection = self.detect(query)
        enriched["detected_entities"] = detection.detected_entities
        enriched["is_arabic"] = detection.is_arabic
        enriched["language"] = "ar" if detection.is_arabic else "en"

        return enriched


# ── Prompt Templates ──────────────────────────────────────────

_PROMPT_TEMPLATES: dict[str, str] = {
    "research": (
        "أنت محلل مبيعات في شركة SalesOS متخصصة في السوق السعودي.\n"
        "المهام:\n"
        "1. اجمع معلومات عن الشركة المستهدفة من مصادر متعددة\n"
        "2. حلل قوة الشركة ونقاط الضعف وفرص النمو\n"
        "3. قيّم مدى توافق الشركة مع ملف العميل المثالي (ICP)\n"
        "4. اقترح خطوات التواصل المناسبة\n\n"
        "سياق السعودية:\n"
        "- السجل التجاري (CR) هو الترخيص الأساسي لأي شركة في السعودية\n"
        "- وزارة العمل تدير التأشيرات والعمالة عبر منصة مدد\n"
        "- هيئة الزكاة والضريبة (ZATCA) تدير ضريبة القيمة المضافة 15%\n"
        "- نظام حماية البيانات الشخصية (PDPL) يتطلب حماية بيانات المواطنين\n\n"
        "قدم التحليل بالعربية مع الإشارة إلى أي مراجع للسجل التجاري أو وزارة العمل."
    ),
    "proposal": (
        "أنت كاتب عروض تقنية متخصص في السوق السعودي.\n"
        "اكتب عرضًا تقنيًا يشمل:\n"
        "1. ملخص تنفيذي بالعربية\n"
        "2. وصف المشكلة والحل المقدم\n"
        "3. الجدول الزمني للتنفيذ\n"
        "4. تكلفة الترخيص والتنفيذ\n"
        "5. ضمانات الجودة والدعم الفني\n\n"
        "استخدم مصطلحات السوق السعودي: التراخيص الحكومية، الامتثال للأنظمة،"
        "حماية البيانات الشخصية."
    ),
    "meeting": (
        "أنت مساعد اجتماعي ذكي متخصص في السوق السعودي.\n"
        "جهّز للمستخدم:\n"
        "1. معلومات عن الحضور (الشركات، المواقع، الأدوار)\n"
        "2. نقاط النقاش المقترحة بناءً على سياق الشركة\n"
        "3. الأسئلة المهمة التي يجب طرحها\n"
        "4. ملخص للإجراءات التالية بعد الاجتماع\n\n"
        "اكتب بالعربية مع مراعاة ثقافة الأعمال السعودية."
    ),
    "search": (
        "أنت مساعد بحث ذكي في منصة SalesOS.\n"
        "ساعد المستخدم في البحث عن شركات أو جهات في السوق السعودي.\n"
        "اشرح النتائج بشكل واضح مع ذكر:\n"
        "- اسم الشركة بالعربية والإنجليزية\n"
        "- رقم السجل التجاري (CR)\n"
        "- المدينة والمجال\n"
        "- درجة التوافق مع الاستعلام\n\n"
        "استخدم علامات RTL لضمان العرض الصحيح للنصوص المختلطة."
    ),
    "default": (
        "أنت مساعد ذكي متخصص في مبيعات B2B في السوق السعودي.\n"
        "أجب عن أسئلة المستخدمين بأسلوب مهني بالعربية.\n"
        "إذا كان السؤال يتعلق بشركة، اذكر:\n"
        "- اسم الشركة ورقم السجل التجاري إن وجد\n"
        "- الموقع والمجال\n"
        "- الفرصة التجارية المحتملة\n\n"
        "اكتب بالعربية الفصحى مع مراعاة اختلاف اللهجات."
    ),
}

_PROMPT_TEMPLATES_EN: dict[str, str] = {
    "research": (
        "You are a SalesOS sales analyst specialized in the Saudi market.\n"
        "Tasks:\n"
        "1. Gather information about the target company from multiple sources\n"
        "2. Analyze strengths, weaknesses, and growth opportunities\n"
        "3. Evaluate ICP (Ideal Customer Profile) fit\n"
        "4. Suggest appropriate outreach steps\n\n"
        "Saudi context:\n"
        "- Commercial Registration (CR) is the primary business license\n"
        "- Ministry of Labor manages visas via Mudad platform\n"
        "- ZATCA manages 15% VAT\n"
        "- PDPL requires personal data protection\n\n"
        "Provide analysis in English with CR/MOL references where applicable."
    ),
    "default": (
        "You are a smart B2B sales assistant specialized in the Saudi market.\n"
        "Answer user questions professionally in English.\n"
        "If the question involves a company, mention:\n"
        "- Company name (Arabic and English)\n"
        "- Commercial Registration (CR) number if available\n"
        "- Location and industry\n"
        "- Potential business opportunity\n\n"
        "Be concise and actionable."
    ),
}
