from datetime import datetime, timezone
import logging
from notion_api import (
    MuhideNotion,
    get_date,
    get_number,
    set_number,
    set_checkbox,
)
from config import DB_IDS, DB_NAMES

logger = logging.getLogger(__name__)


def days_since(date_str: str) -> int:
    if not date_str:
        return -1
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return delta.days
    except (ValueError, TypeError):
        return -1


def run(notion: MuhideNotion) -> None:
    print("=" * 60)
    print("STALE DETECTOR")
    print("كشف البيانات القديمة")
    print("=" * 60)

    db_keys = [
        "sfda",
        "engineering_offices",
        "contractors",
        "suppliers",
        "companies",
        "contacts",
    ]

    for key in db_keys:
        db_id = DB_IDS.get(key)
        if not db_id:
            print(f"\n  [!] {DB_NAMES.get(key, key)}: no database ID")
            continue

        print(f"\n  Scanning {DB_NAMES.get(key, key)}...")
        pages = notion.get_all_pages(db_id)
        print(f"    → {len(pages)} pages")

        stale_count = 0
        updated = 0

        for page in pages:
            props = page["properties"]
            last_activity = get_date(props, "Last Activity Date")
            last_contact = get_date(props, "Last Contact Date")

            days_activity = days_since(last_activity)
            days_contact = days_since(last_contact)

            # Pick the most recent available date
            if days_activity >= 0:
                days = days_activity
            elif days_contact >= 0:
                days = days_contact
            else:
                continue

            is_stale = days > 30

            try:
                notion.update_page(
                    page["id"],
                    {
                        "Days Since Last Activity": set_number(float(days)),
                        "Stale Flag": set_checkbox(is_stale),
                    },
                )
                updated += 1
                if is_stale:
                    stale_count += 1
            except Exception as e:
                logger.warning(
                    "Could not update page %s: %s", page["id"], e
                )

        print(f"    → {updated} pages checked")
        print(f"    → {stale_count} stale ( > 30 days)")

    print(f"\n  ✓ Done! / تم بنجاح")
