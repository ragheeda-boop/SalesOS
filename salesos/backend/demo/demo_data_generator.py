"""Demo data generator — generates demo_data.json with realistic Saudi company data.

Usage:
    python -m demo.demo_data_generator              # Generate fresh demo data
    python -m demo.demo_data_generator --force       # Overwrite existing
"""

import argparse
import json
import os
import sys

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_demo_data(force: bool = False) -> dict:
    output_path = os.path.join(DEMO_DIR, "demo_data.json")
    if os.path.exists(output_path) and not force:
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)

    from demo.seed_data import seed_data
    return seed_data(base_dir=DEMO_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SalesOS demo data")
    parser.add_argument("--force", action="store_true", help="Overwrite existing demo_data.json")
    args = parser.parse_args()

    data = generate_demo_data(force=args.force)
    total = data.get("total", {})
    print(f"\nDone: {total.get('companies', 0)} companies, {total.get('opportunities', 0)} opportunities")
    sys.exit(0)
