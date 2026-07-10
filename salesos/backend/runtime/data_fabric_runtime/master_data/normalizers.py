"""Normalizer Engine — city, CR format, and Arabic/English text normalizers.

These are used by the Data Fabric pipeline Normalizer stage to standardize
record fields before validation and entity resolution.
"""

from __future__ import annotations

import re

from runtime.data_fabric_runtime.master_data import CityLookup

# Single shared instance
_city_lookup = CityLookup()


def normalize_city(city_name: str | None) -> str | None:
    """Normalize a city name to canonical Arabic form."""
    normalized = normalize_arabic_text(city_name)
    return _city_lookup.normalize(normalized)


def normalize_cr(cr_number: str | None) -> str | None:
    """Normalize a CR number to canonical 10-digit format."""
    if not cr_number:
        return None
    cleaned = re.sub(r"\s+", "", cr_number.strip())
    # Convert Arabic-Indic digits (٠-٩) and Extended digits (۰-۹) to ASCII
    cleaned = re.sub(r"[\u0660-\u0669]", lambda m: str(ord(m.group(0)) - 0x0660), cleaned)
    cleaned = re.sub(r"[\u06F0-\u06F9]", lambda m: str(ord(m.group(0)) - 0x06F0), cleaned)
    cleaned = re.sub(r"[^0-9]", "", cleaned)
    if not cleaned:
        return None
    if len(cleaned) > 10:
        cleaned = cleaned[:10]
    return cleaned.zfill(10)


def normalize_arabic_text(text: str | None) -> str | None:
    """Normalize Arabic text: unify alef, yeh, teh, remove diacritics, normalize digits."""
    if not text:
        return None
    text = text.strip()
    # Phase 1: Character normalization
    # Unify alef forms (hamza above/below, madd, wasla → bare alef)
    text = re.sub(r"[أإآٱ]", "ا", text)
    # Unify alef maqsura → yaa
    text = re.sub(r"[ى]", "ي", text)
    # Unify teh marbuta → heh
    text = re.sub(r"[ة]", "ه", text)
    # Unify waw with hamza → waw
    text = re.sub(r"[ؤ]", "و", text)
    # Unify yeh with hamza → yaa
    text = re.sub(r"[ئ]", "ي", text)
    # Unify keheh → kaf (Persian/Urdu)
    text = re.sub(r"[ک]", "ك", text)
    # Unify heh goal → heh (Urdu)
    text = re.sub(r"[ہ]", "ه", text)

    # Phase 2: Remove diacritics / tashkeel
    text = re.sub(r"[\u064B-\u065F\u0610-\u061A\u0670]", "", text)

    # Phase 3: Normalize Arabic-Indic digits to ASCII
    text = re.sub(r"[\u0660-\u0669]", lambda m: str(ord(m.group(0)) - 0x0660), text)
    text = re.sub(r"[\u06F0-\u06F9]", lambda m: str(ord(m.group(0)) - 0x06F0), text)

    # Phase 4: Remove tatweel (kashida)
    text = re.sub(r"ـ", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_field(value: str | None, field_type: str = "text") -> str | None:
    """Dispatch to the right normalizer based on field type."""
    if value is None:
        return None
    mapping = {
        "city": normalize_city,
        "cr_number": normalize_cr,
        "arabic_text": normalize_arabic_text,
    }
    normalizer = mapping.get(field_type)
    if normalizer:
        return normalizer(value)
    return value.strip() if isinstance(value, str) else value
