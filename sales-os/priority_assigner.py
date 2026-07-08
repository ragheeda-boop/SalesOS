import logging
from notion_api import (
    MuhideNotion,
    get_number,
    get_checkbox,
    get_select,
    get_rich_text,
    set_select,
)
from config import DB_IDS, DB_NAMES

logger = logging.getLogger(__name__)


def _score(props: dict) -> float:
    return get_number(props, "Data Completeness Score") or 0


def _ready(props: dict) -> bool:
    return get_checkbox(props, "Ready For Outreach")


def _positive_signal(props: dict) -> bool:
    return get_checkbox(props, "Positive Signal")


def _classification(props: dict) -> str:
    return get_select(props, "Classification Grade") or get_rich_text(
        props, "Classification Grade"
    ) or ""


def _is_complete(props: dict, threshold: float = 80) -> bool:
    return _score(props) >= threshold


def _assign_sfda(props: dict) -> str:
    s = _score(props)
    if s >= 70 and _ready(props):
        return "P1"
    if s >= 40:
        return "P2"
    return "P3"


def _assign_eo(props: dict) -> str:
    if _is_complete(props) and _positive_signal(props):
        return "High"
    if _is_complete(props):
        return "Medium"
    return "Low"


def _assign_contractor(props: dict) -> str:
    cls = _classification(props)
    first_second = any(
        kw in cls for kw in ["أولى", "ثانية", "اولى", "ثانية"]
    )
    if first_second and _is_complete(props):
        return "P1"
    third_fourth = any(
        kw in cls for kw in ["ثالثة", "رابعة", "ثالثه", "رابعه", "ثالث", "رابع"]
    )
    if third_fourth or _is_complete(props):
        return "P2"
    return "P3"


ASSIGNERS = {
    "sfda": _assign_sfda,
    "engineering_offices": _assign_eo,
    "contractors": _assign_contractor,
    "suppliers": lambda p: _assign_sfda(p),
}


def run(notion: MuhideNotion) -> None:
    print("=" * 60)
    print("PRIORITY ASSIGNER")
    print("محدد الأولويات")
    print("=" * 60)

    db_keys = ["sfda", "engineering_offices", "contractors", "suppliers"]

    for key in db_keys:
        db_id = DB_IDS.get(key)
        if not db_id:
            print(f"\n  [!] {DB_NAMES.get(key, key)}: no database ID")
            continue

        assign = ASSIGNERS.get(key)
        if not assign:
            print(f"\n  [!] {DB_NAMES.get(key, key)}: no rule defined")
            continue

        print(f"\n  Assigning for {DB_NAMES.get(key, key)}...")
        pages = notion.get_all_pages(db_id)
        print(f"    → {len(pages)} pages")

        updated = 0
        counts = {}

        for page in pages:
            props = page["properties"]
            priority = assign(props)
            counts[priority] = counts.get(priority, 0) + 1

            try:
                notion.update_page(
                    page["id"],
                    {"Priority": set_select(priority)},
                )
                updated += 1
            except Exception as e:
                logger.warning(
                    "Could not update page %s: %s", page["id"], e
                )

        print(f"    → {updated} pages updated")
        for p, c in sorted(counts.items()):
            print(f"       {p}: {c}")

    print(f"\n  ✓ Done! / تم بنجاح")
