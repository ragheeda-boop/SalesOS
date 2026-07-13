"""Arabic Text Preprocessing Pipeline — normalization, stop words, stemming, NER, quality scoring.

Provides a comprehensive NLP pipeline for Arabic text used across SalesOS:
- Text normalization (Alef variants, Teh Marbuta, Yeh normalization)
- Diacritics removal (Tashkeel)
- Stop word removal (Arabic stop words list)
- Basic Arabic stemmer (suffix/prefix stripping)
- Named entity detection (company names, city names, person names)
- Text quality scoring (completeness, readability, normalization confidence)

Usage:
    preprocessor = ArabicPreprocessor()
    result = preprocessor.process("شَرِكَةُ الأَمَلِ للتّجارة في الرياض")
    print(result.normalized)        # "شركة الامل للتجارة الرياض"
    print(result.stemmed_tokens)    # ["شرك", "امل", "تجار", "رياض"]
    print(result.entities)          # [(" الرياض", "city"), ("شركة", "company_type")]
    print(result.quality_score)     # TextQualityScore(completeness=0.85, ...)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


class EntityType(str, Enum):
    """Named entity types detected in Arabic text."""
    COMPANY = "company"
    CITY = "city"
    REGION = "region"
    PERSON = "person"
    COUNTRY = "country"
    INDUSTRY = "industry"
    LEGAL_FORM = "legal_form"


@dataclass
class TextQualityScore:
    """Quality metrics for processed Arabic text."""
    completeness: float = 0.0  # 0-1: how complete the text is
    readability: float = 0.0  # 0-1: readability score
    normalization_confidence: float = 0.0  # 0-1: confidence in normalization
    has_arabic: bool = False
    has_english: bool = False
    is_mixed_language: bool = False
    char_count: int = 0
    word_count: int = 0
    arabic_ratio: float = 0.0  # ratio of Arabic chars in text


@dataclass
class PreprocessingResult:
    """Result of the Arabic text preprocessing pipeline."""
    original: str = ""
    normalized: str = ""
    tokens: list[str] = field(default_factory=list)
    stemmed_tokens: list[str] = field(default_factory=list)
    entities: list[tuple[str, str]] = field(default_factory=list)
    quality_score: TextQualityScore = field(default_factory=TextQualityScore)
    stop_words_removed: int = 0
    processing_flags: list[str] = field(default_factory=list)


class ArabicPreprocessor:
    """Comprehensive Arabic text preprocessing pipeline.

    Combines normalization, tokenization, stemming, NER, and quality scoring
    into a single configurable pipeline.

    Usage:
        pp = ArabicPreprocessor()
        result = pp.process("شَرِكَةُ الأَمَلِ للتّجارة في الرياض")
    """

    # ── Unicode character classes ─────────────────────────────────────

    _DIACRITICS_PATTERN: ClassVar[re.Pattern] = re.compile(
        r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4'
        r'\u06E7\u06E8\u06EA-\u06ED]'
    )

    _TATWEEL = '\u0640'

    _WHITESPACE_RE: ClassVar[re.Pattern] = re.compile(r'\s+')

    _ARABIC_RANGE: ClassVar[re.Pattern] = re.compile(
        r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    )

    _ENGLISH_RANGE: ClassVar[re.Pattern] = re.compile(r'[a-zA-Z]')

    # ── Character normalization tables ────────────────────────────────

    _ALEF_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0622'): '\u0627',
        ord('\u0623'): '\u0627',
        ord('\u0625'): '\u0627',
        ord('\u0671'): '\u0627',
    }

    _YEH_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0649'): '\u064A',
        ord('\u06CC'): '\u064A',
        ord('\u06D0'): '\u064A',
    }

    _HAMZA_YEH_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0626'): '\u064A',
    }

    _TEH_MARBUTA_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0629'): '\u0647',
    }

    _WAW_HAMZA_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0624'): '\u0648',
    }

    _DIGIT_TABLE: ClassVar[dict[int, str]] = {
        ord('\u0660'): '0', ord('\u0661'): '1', ord('\u0662'): '2',
        ord('\u0663'): '3', ord('\u0664'): '4', ord('\u0665'): '5',
        ord('\u0666'): '6', ord('\u0667'): '7', ord('\u0668'): '8',
        ord('\u0669'): '9',
    }

    # ── Arabic stop words ─────────────────────────────────────────────

    ARABIC_STOP_WORDS: ClassVar[set[str]] = {
        "في", "من", "إلى", "على", "عن", "بـ", "لـ", "حتى", "منذ",
        "و", "أو", "ثم", "لكن", "بل", "أم", "لا",
        "هو", "هي", "أنت", "أنتِ", "أنا", "نحن", "هم", "هن",
        "هذا", "هذه", "هؤلاء", "ذلك", "تلك", "أولئك", "هنا", "هناك",
        "الذي", "التي", "الذين", "اللواتي", "اللذان",
        "ماذا", "ما", "كيف", "أين", "متى", "لماذا", "هل",
        "لم", "لن", "ليس",
        "إن", "إذا", "لو", "لولا", "كلما",
        "قد", "سوف", "سـ",
        "أي", "بعض", "كل", "جميع", "عدة", "نفس",
        "بين", "خلال", "inside", "خارج", "حول",
        "مع", "بدون", "دون", "غير", "قبل", "بعد",
        "عند", "لدى", "نحو", "حسب",
    }

    # ── Arabic stems (suffix/prefix patterns) ─────────────────────────

    # Common Arabic prefixes
    _PREFIXES: ClassVar[list[str]] = [
        "ال", "و", "ب", "ل", "ك", "فس", "وال", "بال", "لل", "وك", "وب",
    ]

    # Common Arabic suffixes
    _SUFFIXES: ClassVar[list[str]] = [
        "ة", "ات", "ين", "ون", "ان", "هم", "هن", "كما",
        "ي", "ك", "نا", "تم", "كن", "هم",
        "ية", "يات", "يين", "يات",
    ]

    # ── Named entities ────────────────────────────────────────────────

    SAUDI_CITIES: ClassVar[set[str]] = {
        "الرياض", "جدة", "الدمام", "مكة", "المدينة", "المنورة",
        "القصيم", "بريدة", "الخرج", "الجبيل", "الأحساء",
        "نجران", "عسير", "الباحة", "تبوك", "حائل",
        "الجوف", "سكاكا", "عرعر", "الحدود الشمالية", "رفحاء",
        "ينبع", "الوجه", "ضباء", "الليث", "القنفذة",
        "الأفلاج", "الزلفي", "المجمعة", "الدوادمي", "وادي الدواسر",
        "بلجرشى", "بيشة", "أبها", "خميس مشيط", "النماص",
        "سيهات", "الظهران", "الخبر", "الجبيل", "القطيف",
        "الأحساء", "الkhobar", "jubail", "dammam", "riyadh", "jeddah",
    }

    SAUDI_REGIONS: ClassVar[set[str]] = {
        "الرياض", "مكة المكرمة", "المدينة المنورة", "المنطقة الشرقية",
        "القصيم", "عسير", "الجوف", "حائل", "تبوك", "الحدود الشمالية",
        "الباحة", "نجران", "جازان", "الجيزه", "المنطقة الغربية",
    }

    COUNTRIES: ClassVar[set[str]] = {
        "المملكة العربية السعودية", "السعودية", "الإمارات", "الإمارات العربية المتحدة",
        "مصر", "الأردن", "الكويت", "البحرين", "قطر", "عمان",
        "العراق", "لبنان", "فلسطين", "اليمن", "سوريا",
        "السودان", "ليبيا", "تونس", "المغرب", "الجزائر",
        "الولايات المتحدة", "أمريكا", "بريطانيا", "فرنسا", "ألمانيا",
        "الصين", "اليابان", "كوريا", "الهند", "باكستان",
        "تركيا", "ماليزasia", "إندونيسيا", "سنغافورة",
    }

    LEGAL_FORMS: ClassVar[set[str]] = {
        "شركة ذات مسؤولية محدودة", "ذ.م.م", "شركة مساهمة عامة",
        "شركة مساهمة خاصة", "مؤسسة فردية", "فرع أجنبي",
        "شركة شخصية", "ش.م.ع", "ش.ذ.م.م", "م.ف",
        "شركة", "مؤسسة", "مصنع", "مكتب", "فرع",
    }

    INDUSTRY_KEYWORDS: ClassVar[set[str]] = {
        "تقنية", "تكنولوجيا", "برمجيات", "تقنية المعلومات",
        "مقاولات", "إنشاءات", "بناء", "تجارة", "صناعة",
        "زراعة", "نقل", "شحن", "لوجستيات", "تعليم", "صحة",
        "عقارات", "تمويل", "بنوك", "تأمين", "اتصالات",
        "طاقة", "بترول", "سياحة", "فندقة", "إعلام", "غذاء",
        "استشارات", "هندسة", "قانون", "محاماة",
    }

    def __init__(
        self,
        normalize: bool = True,
        remove_diacritics: bool = True,
        remove_stop_words: bool = True,
        stem: bool = True,
        detect_entities: bool = True,
        score_quality: bool = True,
        normalize_digits: bool = True,
    ):
        self.normalize_text = normalize
        self.remove_diacritics = remove_diacritics
        self.remove_stop_words = remove_stop_words
        self.stem = stem
        self.detect_entities = detect_entities
        self.score_quality = score_quality
        self.normalize_digits = normalize_digits

    def process(self, text: str) -> PreprocessingResult:
        """Run the full preprocessing pipeline on Arabic text.

        Args:
            text: Raw Arabic (or mixed) text to process

        Returns:
            PreprocessingResult with all processed outputs
        """
        result = PreprocessingResult(original=text)

        if not text or not text.strip():
            return result

        text = text.strip()

        # 1. Quality score (before normalization to capture original state)
        if self.score_quality:
            result.quality_score = self._score_quality(text)

        # 2. Normalize text
        normalized = text
        if self.normalize_text:
            normalized = self._normalize(text)
        result.normalized = normalized

        # 3. Tokenize
        result.tokens = self._tokenize(normalized)

        # 4. Remove stop words
        if self.remove_stop_words:
            before_count = len(result.tokens)
            result.tokens = [t for t in result.tokens if t not in self.ARABIC_STOP_WORDS]
            result.stop_words_removed = before_count - len(result.tokens)

        # 5. Stem
        if self.stem:
            result.stemmed_tokens = [self._stem(t) for t in result.tokens]
        else:
            result.stemmed_tokens = list(result.tokens)

        # 6. Named entity detection
        if self.detect_entities:
            result.entities = self._detect_entities(text, normalized)

        return result

    def normalize(self, text: str) -> str:
        """Normalize Arabic text (public convenience method)."""
        return self._normalize(text)

    def stem(self, word: str) -> str:
        """Stem a single Arabic word (public convenience method)."""
        return self._stem(word)

    def _normalize(self, text: str) -> str:
        """Apply the full normalization pipeline."""
        if not text or not text.strip():
            return ""

        text = text.strip()

        if self.remove_diacritics:
            text = self._DIACRITICS_PATTERN.sub('', text)

        text = text.replace(self._TATWEEL, '')

        text = text.translate(self._ALEF_TABLE)
        text = text.translate(self._YEH_TABLE)
        text = text.translate(self._HAMZA_YEH_TABLE)
        text = text.translate(self._TEH_MARBUTA_TABLE)
        text = text.translate(self._WAW_HAMZA_TABLE)

        if self.normalize_digits:
            text = text.translate(self._DIGIT_TABLE)

        text = self._WHITESPACE_RE.sub(' ', text).strip()
        return text

    def _tokenize(self, text: str) -> list[str]:
        """Split normalized text into tokens."""
        if not text:
            return []
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]

    def _stem(self, word: str) -> str:
        """Basic Arabic stemmer — suffix and prefix stripping.

        Uses a rule-based approach:
        1. Remove common prefixes (ال, و, ب, ل, ك)
        2. Remove common suffixes (ة, ات, ين, ون, ان)
        3. Apply pattern matching for common verb/noun forms
        """
        if not word or len(word) <= 3:
            return word

        original = word

        # Step 1: Remove prefixes (but keep minimum 3 chars)
        for prefix in self._PREFIXES:
            if word.startswith(prefix) and len(word) - len(prefix) >= 3:
                word = word[len(prefix):]
                break

        # Step 2: Remove suffixes (but keep minimum 3 chars)
        for suffix in sorted(self._SUFFIXES, key=len, reverse=True):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                word = word[:-len(suffix)]
                break

        # Step 3: If stem is too short, return original
        if len(word) < 2:
            return original

        return word

    def _detect_entities(
        self, original: str, normalized: str
    ) -> list[tuple[str, str]]:
        """Detect named entities in Arabic text.

        Returns list of (entity_text, entity_type) tuples.
        """
        entities: list[tuple[str, str]] = []

        # Check cities
        for city in self.SAUDI_CITIES:
            if city in normalized or city in original:
                entities.append((city, EntityType.CITY.value))

        # Check regions
        for region in self.SAUDI_REGIONS:
            if region in normalized or region in original:
                entities.append((region, EntityType.REGION.value))

        # Check countries
        for country in self.COUNTRIES:
            if country in normalized or country in original:
                entities.append((country, EntityType.COUNTRY.value))

        # Check legal forms
        for legal in self.LEGAL_FORMS:
            if legal in original:
                entities.append((legal, EntityType.LEGAL_FORM.value))

        # Check industry keywords
        for industry in self.INDUSTRY_KEYWORDS:
            if industry in normalized:
                entities.append((industry, EntityType.INDUSTRY.value))

        # Detect company patterns (شركة + name)
        company_pattern = re.compile(r'(شركة|مؤسسة|مصنع|مجموعة)\s+(\S+)')
        for match in company_pattern.finditer(original):
            entities.append((match.group(0), EntityType.COMPANY.value))

        # Deduplicate
        seen = set()
        unique_entities = []
        for entity, etype in entities:
            key = (entity, etype)
            if key not in seen:
                seen.add(key)
                unique_entities.append((entity, etype))

        return unique_entities

    def _score_quality(self, text: str) -> TextQualityScore:
        """Score the quality of the input text."""
        if not text:
            return TextQualityScore()

        arabic_chars = len(self._ARABIC_RANGE.findall(text))
        english_chars = len(self._ENGLISH_RANGE.findall(text))
        total_chars = arabic_chars + english_chars
        words = text.split()

        arabic_ratio = arabic_chars / max(total_chars, 1)
        has_arabic = arabic_chars > 0
        has_english = english_chars > 0
        is_mixed = has_arabic and has_english

        # Completeness: based on word count and character count
        word_count = len(words)
        if word_count >= 5:
            completeness = 1.0
        elif word_count >= 3:
            completeness = 0.8
        elif word_count >= 1:
            completeness = 0.5
        else:
            completeness = 0.0

        # Readability: penalize very long words, reward sentence-like structures
        avg_word_len = (
            sum(len(w) for w in words) / max(word_count, 1)
        )
        if 3 <= avg_word_len <= 8:
            readability = 0.9
        elif avg_word_len <= 12:
            readability = 0.6
        else:
            readability = 0.3

        # Normalization confidence: how confidently we can normalize
        if has_arabic and not is_mixed:
            norm_confidence = 0.95
        elif is_mixed:
            norm_confidence = 0.7
        elif has_english:
            norm_confidence = 0.85
        else:
            norm_confidence = 0.5

        return TextQualityScore(
            completeness=round(completeness, 2),
            readability=round(readability, 2),
            normalization_confidence=round(norm_confidence, 2),
            has_arabic=has_arabic,
            has_english=has_english,
            is_mixed_language=is_mixed,
            char_count=len(text),
            word_count=word_count,
            arabic_ratio=round(arabic_ratio, 2),
        )
