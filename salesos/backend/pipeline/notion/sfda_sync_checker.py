from datetime import datetime, timezone
import logging
from notion_api import (
    MuhideNotion,
    get_date,
    get_title,
    set_select,
    set_checkbox,
)
from config import DB_IDS

logger = logging.getLogger(__name__)


def run(notion: MuhideNotion) -> None:
    print("=" * 60)
    print("SFDA SYNC CHECKER")
    print("مدقق تراخيص الهيئة")
    print("=" * 60)

    db_id = DB_IDS.get("sfda")
    if not db_id:
        print("\n  [!] SFDA database ID not found in config")
        return

    print(f"\n  Scanning SFDA database for expired licenses...")
    pages = notion.get_all_pages(db_id)
    print(f"    → {len(pages)} pages loaded")

    expired = 0
    expiring_soon = 0
    valid = 0
    no_date = 0
    now = datetime.now(timezone.utc)

    for page in pages:
        props = page["properties"]
        name = get_title(props, "Company Name")
        expiry_str = get_date(props, "License Expiry Date")

        if not expiry_str:
            no_date += 1
            continue

        try:
            expiry_dt = datetime.fromisoformat(
                expiry_str.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            no_date += 1
            continue

        if expiry_dt < now:
            status = "Expired"
            expired += 1
        elif (expiry_dt - now).days <= 30:
            status = "Expiring Soon"
            expiring_soon += 1
        else:
            status = "Valid"
            valid += 1

        try:
            notion.update_page(
                page["id"],
                {
                    "License Status": set_select(status),
                    "Needs Review": set_checkbox(status != "Valid"),
                },
            )
        except Exception as e:
            logger.warning(
                "Could not update page %s (%s): %s", page["id"], name, e
            )

    print(f"\n  Results / النتائج:")
    print(f"    Expired / منتهي         : {expired}")
    print(f"    Expiring Soon / ينتهي قريباً: {expiring_soon}")
    print(f"    Valid / ساري            : {valid}")
    print(f"    No expiry date / بدون تاريخ: {no_date}")

    if expired or expiring_soon:
        print(f"\n  ⚠  {expired + expiring_soon} license(s) need attention!")

    print(f"\n  ✓ Done! / تم بنجاح")
