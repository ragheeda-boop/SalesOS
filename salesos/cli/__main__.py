"""SalesOS CLI entry point: `python -m cli create module <name>`."""

import argparse
import sys

from .generator import create_module


def main() -> None:
    parser = argparse.ArgumentParser(prog="salesos", description="SalesOS Internal Developer Platform CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create new resources")
    create_subparsers = create_parser.add_subparsers(dest="resource", required=True)

    module_parser = create_subparsers.add_parser("module", help="Create a new module")
    module_parser.add_argument("name", help="Module name (e.g., 'opportunity')")
    module_parser.add_argument("--entity", "-e", required=True, help="Entity name (e.g., 'Opportunity')")
    module_parser.add_argument("--schema", "-s", default="public", help="Database schema (default: public)")
    module_parser.add_argument("--label-ar", help="Arabic label for the entity")
    module_parser.add_argument("--description", help="English description")
    module_parser.add_argument("--description-ar", help="Arabic description")
    module_parser.add_argument("--path", default="backend", help="Base path (default: backend)")

    args = parser.parse_args()

    if args.command == "create" and args.resource == "module":
        path = create_module(
            base_path=args.path,
            module=args.name,
            entity=args.entity,
            schema=args.schema,
            label_ar=args.label_ar,
            description=args.description or "",
            description_ar=args.description_ar or "",
        )
        print(f"Module created at: {path}")
        sys.exit(0)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
