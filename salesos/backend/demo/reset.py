"""Demo Environment Reset — truncates and re-seeds all demo data.

Usage:
    python -m backend.demo.reset              # Reset demo data
    python -m backend.demo.reset --seed-only   # Only regenerate seed file
"""

import argparse
import json
import os
import sys


DEMO_DATA_FILE = os.path.join(os.path.dirname(__file__), "demo_data.json")


def reset_demo_data(base_dir: str | None = None) -> dict:
    """Truncate and re-seed all demo data. Regenerates seed file."""
    from demo.seed_data import seed_data

    demo_dir = base_dir or os.path.dirname(__file__)

    print("=" * 60)
    print("  SalesOS Demo Environment Reset")
    print("=" * 60)

    print("\n  [1/2] Generating fresh seed data...")
    data = seed_data(base_dir=demo_dir)

    print(f"\n  [2/2] Demo data generated successfully.")
    print(f"  Companies:     {data['total']['companies']}")
    print(f"  Opportunities: {data['total']['opportunities']}")
    print(f"  Meetings:      {data['total']['meetings']}")
    print(f"  Emails:        {data['total']['emails']}")
    print(f"  Signals:       {data['total']['signals']}")
    print(f"  Tasks:         {data['total']['tasks']}")
    print(f"  NBA Recs:      {data['total']['nba_recommendations']}")
    print(f"  Workflows:     {data['total']['workflow_templates']}")
    print(f"  RAG Docs:      {data['total']['rag_documents']}")
    print(f"  Analytics:     {data['total']['dashboard_analytics']}")
    print(f"  Timeline:      {data['total']['timeline_events']}")
    print()
    print("  [DONE] Demo environment has been reset and re-seeded.")

    return data


def load_demo_data() -> dict | None:
    """Load existing demo data from JSON file."""
    if not os.path.exists(DEMO_DATA_FILE):
        return None
    with open(DEMO_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def is_demo_data_available() -> bool:
    """Check if demo seed data file exists."""
    return os.path.exists(DEMO_DATA_FILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset SalesOS demo environment")
    parser.add_argument("--seed-only", action="store_true", help="Only regenerate seed file")
    args = parser.parse_args()

    if args.seed_only:
        from demo.seed_data import seed_data
        seed_data()
    else:
        reset_demo_data()
