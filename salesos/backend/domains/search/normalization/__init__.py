"""Search Normalization — text preprocessing for Arabic and English search queries.

Provides:
- ArabicSearchNormalizer: Comprehensive Arabic text normalization (Alef, Yeh, Teh Marbuta, etc.)
- ArabicStemmer: Lightweight rule-based suffix stripping for Arabic search
- ArabicStopWords: Stop words list for Arabic search
- ArabicSearchThesaurus: Business term synonyms for query expansion
- CompanyNameMatcher: Fuzzy matching of Arabic company names with Jaro-Winkler
"""

from .arabic_normalizer import ArabicSearchNormalizer
from .arabic_stemmer import ArabicStemmer
from .arabic_thesaurus import ArabicSearchThesaurus
from .company_matcher import CompanyMatchResult, CompanyNameMatcher
from .stop_words import ARABIC_STOP_WORDS, STOP_WORDS_RE

__all__ = [
    "ArabicSearchNormalizer",
    "ArabicStemmer",
    "ArabicSearchThesaurus",
    "CompanyMatchResult",
    "CompanyNameMatcher",
    "ARABIC_STOP_WORDS",
    "STOP_WORDS_RE",
]
