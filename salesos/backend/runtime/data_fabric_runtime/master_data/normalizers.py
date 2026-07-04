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
    return _city_lookup.normalize(city_name)


def normalize_cr(cr_number: str | None) -> str | None:
    """Normalize a CR number to canonical 10-digit format."""
    if not cr_number:
        return None
    cleaned = re.sub(r"\s+", "", cr_number.strip())
    cleaned = re.sub(r"[^0-9]", "", cleaned)
    if not cleaned:
        return None
    if len(cleaned) > 10:
        cleaned = cleaned[:10]
    return cleaned.zfill(10)


def normalize_arabic_text(text: str | None) -> str | None:
    """Normalize Arabic text: unify alef, teh, etc."""
    if not text:
        return None
    text = text.strip()
    # Unify alef forms to ا
    text = re.sub(r"[أإآٱ]", "ا", text)
    # Unify teh marbuta and heh
    text = re.sub(r"[ة]", "ه", text)
    # Unify waw with hamza
    text = re.sub(r"[ؤ]", "و", text)
    # Unify alef with madd
    text = re.sub(r"[آ]", "ا", text)
    # Remove tatweel (kashida)
    text = re.sub(r"ـ", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text


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
