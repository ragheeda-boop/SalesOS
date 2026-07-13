"""Arabic stop words for search query filtering.

Stop words are common words that add little semantic value and are frequently
removed from search queries to reduce noise and improve relevance.

This list covers:
- Prepositions (في, من, إلى, على, عن, بـ, لـ, حتى)
- Conjunctions (و, أو, ثم, لكن, بل, أم)
- Pronouns (هو, هي, أنت, أنا, نحن, هم, هن)
- Demonstratives (هذا, هذه, هؤلاء, ذلك, تلك, أولئك)
- Question words (ماذا, كيف, أين, متى, لماذا, هل)
- Common Arabic function words and particles
"""

from __future__ import annotations

import re

ARABIC_STOP_WORDS: set[str] = {
    # Prepositions / حروف الجر
    "في", "من", "إلى", "على", "عن", "بـ", "لـ", "حتى", "منذ",
    "مذ", "رب", "خلا", "عدا", "حاشا", "كي", "لعل", "متى",

    # Conjunctions / حروف العطف
    "و", "أو", "ثم", "لكن", "بل", "أم", "لا", "حتى", "الفاء",

    # Pronouns - detached / الضمائر المنفصلة
    "هو", "هي", "أنت", "أنتِ", "أنتما", "أنتم", "أنتن",
    "أنا", "نحن", "هم", "هن", "هما",

    # Demonstratives / أسماء الإشارة
    "هذا", "هذه", "هذان", "هاتان", "هؤلاء",
    "ذلك", "تلك", "ذانك", "تانك", "أولئك",
    "هنا", "هناك", "ثم",

    # Relative pronouns / الأسماء الموصولة
    "الذي", "التي", "الذين", "اللواتي", "اللذان",
    "اللتان", "اللذين", "اللتين", "الذان", "اللائي",

    # Question words / أدوات الاستفهام
    "ماذا", "ما", "كيف", "أين", "متى", "لماذا", "هل",
    "من", "أي", "كم", "أنى", "أيان",

    # Negation / النفي
    "لم", "لن", "ليس", "ما", "لا", "لات", "إن",

    # Conditional / أدوات الشرط
    "إن", "إذا", "لو", "لولا", "كلما", "لما", "إذما",

    # Verbs - common / أفعال شائعة
    "كان", "كانت", "كانوا", "يكون", "تكون", "يكونون",
    "أصبح", "صار", "ليس", "مازال", "مابرح",
    "يوجد", "توجد", "يوجدون",

    # Particles / حروف
    "قد", "سوف", "سـ", "السين", "سـوف",
    "إن", "أن", "كأن", "لكن", "ليت", "لعل",
    "إلا", "غير", "سوى", "بيد",

    # Common words in business search
    "أي", "بعض", "كل", "جميع", "عدة", "نفس",
    "بين", "خلال", "داخل", "خارج", "حول",
    "فوق", "تحت", "أمام", "خلف", "جانب",
    "مع", "بدون", "بغير", "دون", "غير",
    "قبل", "بعد", "أثناء", "عند", "لدى",
    "نحو", "حسب", "طبق",

    # Very common filler words
    "تم", "يتم", "قام", "يقوم", "جاء", "أتى",
    "شيء", "شخص", "مكان", "وقت", "حالة",
}

STOP_WORDS_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(w) for w in sorted(ARABIC_STOP_WORDS, key=len, reverse=True)) + r')\b'
)
