import logging
from notion_api import (
    MuhideNotion,
    get_title,
    get_rich_text,
    get_email,
    get_phone,
    get_number,
    get_select,
    get_multi_select,
    set_number,
)
from config import DB_IDS, DB_NAMES

logger = logging.getLogger(__name__)

# Each database's required fields and their weight per field (100 / count)
REQUIRED_FIELDS = {
    "sfda": {
        "Company Name": ("title", 20),
        "License Number": ("text", 20),
        "Sector": ("select", 20),
        "City": ("select", 20),
        "Email": ("text", 20),
    },
    "engineering_offices": {
        "Company Name": ("title", 20),
        "Main Email": ("email", 20),
        "Mobile": ("phone", 20),
        "CR Number": ("text", 20),
        "City": ("text", 20),
    },
    "contractors": {
        "اسم الشركة": ("title", 20),
        "CR Number": ("text", 20),
        "Region": ("select", 20),
        "Main Email": ("email", 20),
        "Classification Grade": ("select", 20),
    },
    "suppliers": {
        "اسم المورد": ("title", 30),
        "City": ("select", 25),
        "Region": ("select", 25),
        "Products": ("text", 20),
    },
}

FIELD_ACCESSORS = {
    "title": lambda props, f: get_title(props, f),
    "text": lambda props, f: (
        get_rich_text(props, f) or get_title(props, f)
    ),
    "email": lambda props, f: get_email(props, f),
    "phone": lambda props, f: get_phone(props, f),
    "number": lambda props, f: get_number(props, f) is not None,
    "select": lambda props, f: get_select(props, f),
    "multi_select": lambda props, f: len(get_multi_select(props, f)) > 0,
}


def is_field_filled(props: dict, field_name: str, field_type: str) -> bool:
    accessor = FIELD_ACCESSORS.get(field_type, FIELD_ACCESSORS["text"])
    value = accessor(props, field_name)
    if isinstance(value, bool):
        return value
    return bool(value)


def calculate_score(props: dict, db_key: str) -> int:
    fields = REQUIRED_FIELDS.get(db_key)
    if not fields:
        return 0

    score = 0
    for field_name, (field_type, weight) in fields.items():
        if is_field_filled(props, field_name, field_type):
            score += weight
    return min(score, 100)


def run(notion: MuhideNotion) -> None:
    print("=" * 60)
    print("DATA COMPLETENESS SCORER")
    print("مقياس اكتمال البيانات")
    print("=" * 60)

    db_keys = ["sfda", "engineering_offices", "contractors", "suppliers"]

    for key in db_keys:
        db_id = DB_IDS.get(key)
        if not db_id:
            print(f"\n  [!] {DB_NAMES.get(key, key)}: no database ID")
            continue

        print(f"\n  Scoring {DB_NAMES.get(key, key)}...")
        pages = notion.get_all_pages(db_id)
        print(f"    → {len(pages)} pages")

        updated = 0
        for page in pages:
            props = page["properties"]
            score = calculate_score(props, key)
            try:
                notion.update_page(
                    page["id"],
                    {"Data Completeness Score": set_number(float(score))},
                )
                updated += 1
            except Exception as e:
                logger.warning(
                    "Could not update page %s: %s", page["id"], e
                )

        print(f"    → {updated} pages updated with scores")

        # Summary stats
        scores = []
        for page in pages:
            scores.append(calculate_score(page["properties"], key))
        if scores:
            avg = sum(scores) / len(scores)
            complete = sum(1 for s in scores if s == 100)
            poor = sum(1 for s in scores if s < 40)
            print(f"    → Avg score: {avg:.1f} / 100")
            print(f"    → Complete (100): {complete}")
            print(f"    → Poor (< 40): {poor}")

    print(f"\n  ✓ Done! / تم بنجاح")
