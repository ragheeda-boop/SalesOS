import re
import logging
from notion_api import (
    MuhideNotion,
    get_title,
    get_rich_text,
    set_checkbox,
    set_select,
)
from config import DB_IDS, DB_NAMES

logger = logging.getLogger(__name__)

ARABIC_PREFIXES = [
    "شركة",
    "مؤسسة",
    "مجموعة",
    "مكتب",
    "معمل",
    "مصنع",
    "ابو",
    "أبو",
    "ابن",
    "دار",
    "مركز",
    "مختبر",
]


def normalize_name(raw: str) -> str:
    name = raw.strip()
    for prefix in ARABIC_PREFIXES:
        if name.startswith(prefix + " "):
            name = name[len(prefix) :].strip()
            break
    name = re.sub(r"[^\w\s]", "", name)
    return name.upper().strip()


def get_name(props: dict) -> str:
    name = get_title(props, "Company Name")
    if not name:
        name = get_title(props, "اسم الشركة")
    if not name:
        name = get_rich_text(props, "Company Name")
    if not name:
        name = get_rich_text(props, "اسم الشركة")
    return name


def run(notion: MuhideNotion) -> None:
    print("=" * 60)
    print("DUPLICATE SCANNER")
    print("ماسح البيانات المكررة")
    print("=" * 60)

    source_keys = [
        "sfda",
        "engineering_offices",
        "contractors",
        "suppliers",
    ]

    by_norm = {}

    for key in source_keys:
        db_id = DB_IDS.get(key)
        if not db_id:
            print(f"  [!] {DB_NAMES.get(key, key)}: no database ID")
            continue

        print(f"\n  Scanning {DB_NAMES.get(key, key)}...")
        pages = notion.get_all_pages(db_id)
        print(f"    → {len(pages)} pages loaded")

        for page in pages:
            props = page["properties"]
            raw_name = get_name(props)
            if not raw_name:
                continue

            norm = normalize_name(raw_name)
            if not norm:
                continue

            if norm not in by_norm:
                by_norm[norm] = []
            by_norm[norm].append(
                {
                    "page_id": page["id"],
                    "original": raw_name,
                    "source": DB_NAMES.get(key, key),
                    "source_key": key,
                }
            )

    dup_groups = {n: r for n, r in by_norm.items() if len(r) > 1}

    print(f"\n{'─' * 60}")
    print(f"  Unique names      : {len(by_norm)}")
    print(f"  Duplicate groups  : {len(dup_groups)}")
    total_flagged = sum(len(r) for r in dup_groups.values())
    print(f"  Total pages flagged: {total_flagged}")
    print(f"{'─' * 60}")

    if not dup_groups:
        print("\n  ✓ No duplicates found! / لا توجد بيانات مكررة")
        return

    for norm, recs in sorted(dup_groups.items()):
        sources = {r["source"] for r in recs}

        if len(sources) >= 3 or len(recs) >= 4:
            confidence = "High"
        elif len(recs) >= 3:
            confidence = "Medium"
        else:
            confidence = "Medium"

        print(f"\n  [{norm}]")
        for r in recs:
            print(f"    • {r['original']}  ({r['source']})")
            try:
                notion.update_page(
                    r["page_id"],
                    {
                        "Duplicate Suspected": set_checkbox(True),
                        "Match Confidence": set_select(confidence),
                    },
                )
            except Exception as e:
                logger.warning(
                    "Could not update page %s: %s", r["page_id"], e
                )
        print(f"    → Confidence: {confidence}")

    print(f"\n  ✓ Done! / تم بنجاح")
