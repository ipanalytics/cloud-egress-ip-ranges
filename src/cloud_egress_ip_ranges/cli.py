from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sys

from . import __version__
from .builder import build_from_fixtures, build_from_live_sources, write_artifacts
from .explain import explain_lookup
from .feed import load_feed
from .lookup import lookup_ip


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cloud-egress-ip-ranges",
        description="Build and inspect classified cloud egress IP range feeds.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser("build", help="Build generated feed artifacts.")
    build.add_argument("--offline-fixtures", action="store_true", help="Build from checked-in fixtures.")
    build.add_argument("--output-dir", default="dist", help="Output directory.")
    build.add_argument("--azure-service-tags-url", default="", help="Azure Service Tags JSON URL for live builds.")
    build.set_defaults(func=_build)

    lookup = subparsers.add_parser("lookup", help="Return JSON matches for an IP address.")
    lookup.add_argument("ip")
    lookup.add_argument("--feed", default="dist/cloud-egress-ip-ranges.json")
    lookup.set_defaults(func=_lookup)

    explain = subparsers.add_parser("explain", help="Explain matches for an IP address.")
    explain.add_argument("ip")
    explain.add_argument("--feed", default="dist/cloud-egress-ip-ranges.json")
    explain.set_defaults(func=_explain)

    sources = subparsers.add_parser("sources", help="Show source counts from the generated feed.")
    sources.add_argument("--feed", default="dist/cloud-egress-ip-ranges.json")
    sources.set_defaults(func=_sources)

    stats = subparsers.add_parser("stats", help="Show feed and classified list statistics.")
    stats.add_argument("--feed", default="dist/cloud-egress-ip-ranges.json")
    stats.add_argument("--manifest", default="dist/manifest.json")
    stats.set_defaults(func=_stats)

    parser.set_defaults(func=_show_help)
    return parser


def _show_help(args: argparse.Namespace) -> int:
    args.parser.print_help()
    return 0


def _build(args: argparse.Namespace) -> int:
    try:
        records = (
            build_from_fixtures()
            if args.offline_fixtures
            else build_from_live_sources(azure_service_tags_url=args.azure_service_tags_url)
        )
        manifest = write_artifacts(records, Path(args.output_dir), offline=args.offline_fixtures)
    except Exception as exc:
        return _error(str(exc))
    print(json.dumps({"output_dir": args.output_dir, "total_records": manifest["total_records"]}, sort_keys=True))
    return 0


def _lookup(args: argparse.Namespace) -> int:
    try:
        result = lookup_ip(load_feed(args.feed), args.ip)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        return _error(str(exc))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _explain(args: argparse.Namespace) -> int:
    try:
        result = lookup_ip(load_feed(args.feed), args.ip)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        return _error(str(exc))
    print(explain_lookup(result))
    return 0


def _sources(args: argparse.Namespace) -> int:
    try:
        feed = load_feed(args.feed)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        return _error(str(exc))
    print(json.dumps({"sources": feed.source_counts}, indent=2, sort_keys=True))
    return 0


def _stats(args: argparse.Namespace) -> int:
    try:
        feed = load_feed(args.feed)
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return _error(str(exc))
    payload = {
        "schema_version": feed.schema_version,
        "generated_at": feed.generated_at,
        "total_records": len(feed.records),
        "providers": feed.provider_counts,
        "services": feed.service_counts,
        "classified_lists": len(manifest.get("classified", [])),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.set_defaults(parser=parser)
    args = parser.parse_args(argv)
    return int(args.func(args))
