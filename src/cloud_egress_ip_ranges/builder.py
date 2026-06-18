from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .models import EgressRangeRecord, SCHEMA_VERSION, utc_now_iso
from .sources.aws import parse_aws_ip_ranges
from .sources.azure import parse_azure_service_tags
from .sources.cloudflare import parse_cloudflare_api, parse_cloudflare_text
from .sources.google import parse_google_ranges

FIXED_OFFLINE_TIMESTAMP = "2026-06-18T00:00:00Z"
AWS_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
GOOGLE_CLOUD_URL = "https://www.gstatic.com/ipranges/cloud.json"
GOOGLE_GOOG_URL = "https://www.gstatic.com/ipranges/goog.json"
CLOUDFLARE_V4_URL = "https://www.cloudflare.com/ips-v4"
CLOUDFLARE_V6_URL = "https://www.cloudflare.com/ips-v6"
ROOT_JSON = "cloud-egress-ip-ranges.json"
ROOT_CSV = "cloud-egress-ip-ranges.csv"
MANIFEST = "manifest.json"
SOURCES_MARKDOWN = "sources.md"
SOURCE_CATALOG = [
    {
        "provider": "aws",
        "feed": "AWS ip-ranges.json",
        "source_id": "aws_ip_ranges_json",
        "url": AWS_URL,
        "classification": "cloud and AWS service ranges",
        "live": True,
    },
    {
        "provider": "google_cloud",
        "feed": "Google Cloud cloud.json",
        "source_id": "google_cloud_json",
        "url": GOOGLE_CLOUD_URL,
        "classification": "Google Cloud customer external IP ranges",
        "live": True,
    },
    {
        "provider": "google",
        "feed": "Google goog.json",
        "source_id": "google_goog_json",
        "url": GOOGLE_GOOG_URL,
        "classification": "Google-owned provider ranges",
        "live": True,
    },
    {
        "provider": "azure",
        "feed": "Azure Public Service Tags JSON",
        "source_id": "azure_service_tags_public_json",
        "url": "resolved daily from Microsoft Download Center",
        "classification": "Azure service-tag and regional ranges",
        "live": True,
    },
    {
        "provider": "cloudflare",
        "feed": "Cloudflare IPv4 ranges",
        "source_id": "cloudflare_ips",
        "url": CLOUDFLARE_V4_URL,
        "classification": "Cloudflare edge network ranges",
        "live": True,
    },
    {
        "provider": "cloudflare",
        "feed": "Cloudflare IPv6 ranges",
        "source_id": "cloudflare_ips",
        "url": CLOUDFLARE_V6_URL,
        "classification": "Cloudflare edge network ranges",
        "live": True,
    },
]
CSV_FIELDS = [
    "cidr",
    "provider",
    "platform_family",
    "service_hint",
    "serverless_possible",
    "serverless_exact",
    "edge_possible",
    "region",
    "country_hint",
    "source",
    "source_type",
    "confidence",
    "recommended_action",
    "false_positive_risk",
    "last_seen",
    "last_updated",
    "precision_level",
    "network_border_group",
]


def build_from_fixtures(fixtures_dir: Path | str = "tests/fixtures") -> list[EgressRangeRecord]:
    fixtures = Path(fixtures_dir)
    records: list[EgressRangeRecord] = []
    records.extend(parse_aws_ip_ranges(fixtures / "aws-ip-ranges.json"))
    records.extend(parse_google_ranges(fixtures / "google-cloud.json", feed_kind="cloud"))
    records.extend(parse_google_ranges(fixtures / "google-goog.json", feed_kind="goog"))
    records.extend(parse_azure_service_tags(fixtures / "azure-service-tags.json"))
    records.extend(parse_cloudflare_text(fixtures / "cloudflare-ips-v4.txt"))
    records.extend(parse_cloudflare_text(fixtures / "cloudflare-ips-v6.txt"))
    records.extend(parse_cloudflare_api(fixtures / "cloudflare-api.json"))
    return sort_records(records)


def build_from_live_sources(
    *,
    azure_service_tags_url: str,
    aws_url: str = AWS_URL,
    google_cloud_url: str = GOOGLE_CLOUD_URL,
    google_goog_url: str = GOOGLE_GOOG_URL,
    cloudflare_v4_url: str = CLOUDFLARE_V4_URL,
    cloudflare_v6_url: str = CLOUDFLARE_V6_URL,
) -> list[EgressRangeRecord]:
    if not azure_service_tags_url:
        raise ValueError("live build requires --azure-service-tags-url")
    records: list[EgressRangeRecord] = []
    records.extend(parse_aws_ip_ranges(aws_url))
    records.extend(parse_google_ranges(google_cloud_url, feed_kind="cloud"))
    records.extend(parse_google_ranges(google_goog_url, feed_kind="goog"))
    records.extend(parse_azure_service_tags(azure_service_tags_url))
    records.extend(parse_cloudflare_text(cloudflare_v4_url))
    records.extend(parse_cloudflare_text(cloudflare_v6_url))
    return sort_records(records)


def sort_records(records: Iterable[EgressRangeRecord]) -> list[EgressRangeRecord]:
    return sorted(
        records,
        key=lambda record: (
            record.provider,
            record.platform_family,
            record.service_hint,
            record.network.version,
            int(record.network.network_address),
            record.network.prefixlen,
            record.cidr,
        ),
    )


def write_artifacts(records: list[EgressRangeRecord], output_dir: Path, *, offline: bool) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    classified_dir = output_dir / "classified"
    if classified_dir.exists():
        shutil.rmtree(classified_dir)
    classified_dir.mkdir()

    data = [record.to_dict() for record in sort_records(records)]
    timestamp = FIXED_OFFLINE_TIMESTAMP if offline else utc_now_iso()
    write_json(output_dir / ROOT_JSON, {"schema_version": SCHEMA_VERSION, "generated_at": timestamp, "records": data})
    write_csv(output_dir / ROOT_CSV, data)
    classified = write_classified(classified_dir, data)
    write_sources_markdown(output_dir / SOURCES_MARKDOWN, data, timestamp)

    manifest = build_manifest(output_dir, data, classified, timestamp)
    write_json(output_dir / MANIFEST, manifest)
    manifest["checksums"][MANIFEST] = sha256_file(output_dir / MANIFEST)
    write_json(output_dir / MANIFEST, manifest)
    return manifest


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, data: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def write_classified(classified_dir: Path, data: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in data:
        groups[("provider", row["provider"])].append(row)
        groups[("platform_family", row["platform_family"])].append(row)
        groups[("precision_level", row["precision_level"])].append(row)
        groups[("recommended_action", row["recommended_action"])].append(row)
        groups[("service_hint", row["service_hint"])].append(row)

    inventory: list[dict] = []
    for (kind, value), rows in sorted(groups.items()):
        safe_value = slug(value)
        base = classified_dir / kind
        base.mkdir(parents=True, exist_ok=True)
        json_path = base / f"{safe_value}.json"
        txt_path = base / f"{safe_value}.txt"
        payload = {"classification": {"kind": kind, "value": value}, "records": rows}
        write_json(json_path, payload)
        txt_path.write_text("\n".join(row["cidr"] for row in rows) + "\n", encoding="utf-8")
        inventory.append(
            {
                "kind": kind,
                "value": value,
                "json": str(json_path.relative_to(classified_dir.parent)),
                "txt": str(txt_path.relative_to(classified_dir.parent)),
                "records": len(rows),
            }
        )
    return inventory


def build_manifest(output_dir: Path, data: list[dict], classified: list[dict], timestamp: str) -> dict:
    providers = Counter(row["provider"] for row in data)
    sources = Counter(row["source"] for row in data)
    checksums = {
        ROOT_JSON: sha256_file(output_dir / ROOT_JSON),
        ROOT_CSV: sha256_file(output_dir / ROOT_CSV),
        SOURCES_MARKDOWN: sha256_file(output_dir / SOURCES_MARKDOWN),
    }
    for item in classified:
        checksums[item["json"]] = sha256_file(output_dir / item["json"])
        checksums[item["txt"]] = sha256_file(output_dir / item["txt"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "total_records": len(data),
        "provider_counts": dict(sorted(providers.items())),
        "source_counts": dict(sorted(sources.items())),
        "source_catalog": SOURCE_CATALOG,
        "classified": classified,
        "checksums": dict(sorted(checksums.items())),
    }


def write_sources_markdown(path: Path, data: list[dict], timestamp: str) -> None:
    provider_counts = Counter(row["provider"] for row in data)
    source_counts = Counter(row["source"] for row in data)
    lines = [
        "# cloud-egress-ip-ranges source inventory",
        "",
        f"Generated: `{timestamp}`",
        "",
        "| Provider | Feed | Source ID | Records | URL | Classification |",
        "|---|---|---:|---:|---|---|",
    ]
    for source in SOURCE_CATALOG:
        lines.append(
            "| {provider} | {feed} | `{source_id}` | {records} | {url} | {classification} |".format(
                provider=source["provider"],
                feed=source["feed"],
                source_id=source["source_id"],
                records=source_counts.get(source["source_id"], 0),
                url=source["url"],
                classification=source["classification"],
            )
        )
    lines.extend(
        [
            "",
            "## Provider totals",
            "",
            "| Provider | Records |",
            "|---|---:|",
        ]
    )
    for provider, count in sorted(provider_counts.items()):
        lines.append(f"| {provider} | {count} |")
    lines.extend(
        [
            "",
            "The inventory is generated from the same records as the JSON, CSV, and classified list artifacts.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
