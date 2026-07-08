#!/usr/bin/env python3
"""
MUHIDE Sales OS – Notion Automation Suite
نظام مهام مبيعات MUHIDE – أتمتة Notion
"""

import sys
import logging
from config import NOTION_TOKEN

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(message)s",
)


def main():
    # Lazy-import notion wrapper so config errors surface first
    from notion_api import MuhideNotion

    if not NOTION_TOKEN:
        print("=" * 60)
        print("ERROR / خطأ")
        print("=" * 60)
        print("NOTION_TOKEN is not set.")
        print("Please set the environment variable or edit config.py.")
        print("يرجى تعيين متغير البيئة NOTION_TOKEN أو تعديل ملف config.py")
        sys.exit(1)

    notion = MuhideNotion(NOTION_TOKEN)

    while True:
        print("\n" + "=" * 60)
        print("  MUHIDE Sales OS – Notion Automation Suite")
        print("  نظام أتمتة مبيعات MUHIDE")
        print("=" * 60)
        print()
        print("  Select a script to run / اختر البرنامج النصي:")
        print()
        print("  1) Duplicate Scanner / ماسح البيانات المكررة")
        print("  2) Completeness Scorer / مقياس اكتمال البيانات")
        print("  3) Priority Assigner / محدد الأولويات")
        print("  4) Stale Detector / كشف البيانات القديمة")
        print("  5) SFDA Sync Checker / مدقق تراخيص الهيئة")
        print("  6) Run All / تشغيل الكل")
        print("  0) Exit / خروج")
        print()
        choice = input("  Your choice / اختر رقم: ").strip()

        print()

        scripts = {
            "1": ("Duplicate Scanner", "dedup_scanner"),
            "2": ("Completeness Scorer", "completeness_scorer"),
            "3": ("Priority Assigner", "priority_assigner"),
            "4": ("Stale Detector", "stale_detector"),
            "5": ("SFDA Sync Checker", "sfda_sync_checker"),
        }

        if choice == "0":
            print("  Goodbye! / مع السلامة!")
            sys.exit(0)
        elif choice == "6":
            for key in ("1", "2", "3", "4", "5"):
                name, module_name = scripts[key]
                print(f"\n  >>> Running {name}...\n")
                try:
                    mod = __import__(module_name)
                    mod.run(notion)
                except Exception as e:
                    print(f"\n  [!] {name} failed: {e}")
            print(f"\n  ✓ All scripts completed / تم تشغيل الكل بنجاح")
        elif choice in scripts:
            name, module_name = scripts[choice]
            print(f"  >>> Running {name}...\n")
            try:
                mod = __import__(module_name)
                mod.run(notion)
            except Exception as e:
                print(f"\n  [!] Error / خطأ: {e}")
        else:
            print("  Invalid choice / اختيار غير صحيح")

        input("\n  Press Enter to continue / اضغط إنتر للمتابعة...")


if __name__ == "__main__":
    main()
