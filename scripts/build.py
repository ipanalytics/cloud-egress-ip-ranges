#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from cloud_egress_ip_ranges.builder import build_from_fixtures, build_from_live_sources, write_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build cloud egress IP range artifacts.")
    parser.add_argument(
        "--offline-fixtures",
        action="store_true",
        help="Use checked-in fixtures instead of live provider feeds.",
    )
    parser.add_argument("--output-dir", default="dist", help="Directory for generated artifacts.")
    parser.add_argument("--azure-service-tags-url", default="", help="Azure Service Tags JSON URL for live builds.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        records = (
            build_from_fixtures()
            if args.offline_fixtures
            else build_from_live_sources(azure_service_tags_url=args.azure_service_tags_url)
        )
        manifest = write_artifacts(records, Path(args.output_dir), offline=args.offline_fixtures)
    except Exception as exc:
        print(f"build failed: {exc}")
        return 1
    print(
        "wrote {total} records to {out} ({classified} classified files)".format(
            total=manifest["total_records"],
            out=args.output_dir,
            classified=len(manifest["classified"]),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
