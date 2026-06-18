from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .models import EgressRangeRecord, SCHEMA_VERSION, utc_now_iso
from .provider_catalog import provider_catalog
from .sources.atlassian import parse_atlassian_ip_ranges
from .sources.aws import parse_aws_ip_ranges
from .sources.azure import parse_azure_service_tags
from .sources.cloudflare import parse_cloudflare_api, parse_cloudflare_text
from .sources.fastly import parse_fastly_public_ip_list
from .sources.github import parse_github_meta
from .sources.gitlab import parse_gitlab_com_docs
from .sources.google import parse_google_ranges
from .sources.oracle import parse_oracle_public_ip_ranges
from .sources.stripe import parse_stripe_ips

FIXED_OFFLINE_TIMESTAMP = "2026-06-18T00:00:00Z"
AWS_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
GOOGLE_CLOUD_URL = "https://www.gstatic.com/ipranges/cloud.json"
GOOGLE_GOOG_URL = "https://www.gstatic.com/ipranges/goog.json"
CLOUDFLARE_V4_URL = "https://www.cloudflare.com/ips-v4"
CLOUDFLARE_V6_URL = "https://www.cloudflare.com/ips-v6"
ORACLE_URL = "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json"
FASTLY_URL = "https://api.fastly.com/public-ip-list"
GITHUB_META_URL = "https://api.github.com/meta"
GITLAB_DOCS_URL = "https://docs.gitlab.com/user/gitlab_com/"
ATLASSIAN_URL = "https://ip-ranges.atlassian.com/"
STRIPE_WEBHOOKS_URL = "https://stripe.com/files/ips/ips_webhooks.json"
STRIPE_API_URL = "https://stripe.com/files/ips/ips_api.json"
ROOT_JSON = "cloud-egress-ip-ranges.json"
ROOT_CSV = "cloud-egress-ip-ranges.csv"
MANIFEST = "manifest.json"
SOURCES_MARKDOWN = "sources.md"
PROVIDER_CATALOG_JSON = "provider-catalog.json"
PROVIDER_CATALOG_MARKDOWN = "provider-catalog.md"
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
        "provider": "oracle_cloud",
        "feed": "Oracle OCI public_ip_ranges.json",
        "source_id": "oracle_public_ip_ranges_json",
        "url": ORACLE_URL,
        "classification": "Oracle Cloud regional public IP ranges",
        "live": True,
    },
    {
        "provider": "cloudflare",
        "feed": "Cloudflare IPv4 ranges",
        "source_id": "cloudflare_ips_v4",
        "url": CLOUDFLARE_V4_URL,
        "classification": "Cloudflare edge network ranges",
        "live": True,
    },
    {
        "provider": "cloudflare",
        "feed": "Cloudflare IPv6 ranges",
        "source_id": "cloudflare_ips_v6",
        "url": CLOUDFLARE_V6_URL,
        "classification": "Cloudflare edge network ranges",
        "live": True,
    },
    {
        "provider": "fastly",
        "feed": "Fastly public IP list",
        "source_id": "fastly_public_ip_list",
        "url": FASTLY_URL,
        "classification": "Fastly edge/CDN and Compute possible ranges",
        "live": True,
    },
    {
        "provider": "github",
        "feed": "GitHub Meta API",
        "source_id": "github_meta_api",
        "url": GITHUB_META_URL,
        "classification": "GitHub Actions, hooks, pages, API, git, and web ranges",
        "live": True,
    },
    {
        "provider": "gitlab",
        "feed": "GitLab.com IP range docs",
        "source_id": "gitlab_com_docs",
        "url": GITLAB_DOCS_URL,
        "classification": "GitLab.com Web/API and webhook source ranges",
        "live": True,
    },
    {
        "provider": "atlassian",
        "feed": "Atlassian Cloud IP ranges",
        "source_id": "atlassian_ip_ranges_json",
        "url": ATLASSIAN_URL,
        "classification": "Atlassian Cloud egress ranges",
        "live": True,
    },
    {
        "provider": "stripe",
        "feed": "Stripe webhook IPs",
        "source_id": "stripe_webhook_ips_json",
        "url": STRIPE_WEBHOOKS_URL,
        "classification": "Stripe webhook source IPs",
        "live": True,
    },
    {
        "provider": "stripe",
        "feed": "Stripe API IPs",
        "source_id": "stripe_api_ips_json",
        "url": STRIPE_API_URL,
        "classification": "Stripe API source IPs",
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
    records.extend(parse_oracle_public_ip_ranges(fixtures / "oracle-public-ip-ranges.json"))
    records.extend(parse_cloudflare_text(fixtures / "cloudflare-ips-v4.txt", source_label="cloudflare_ips_v4"))
    records.extend(parse_cloudflare_text(fixtures / "cloudflare-ips-v6.txt", source_label="cloudflare_ips_v6"))
    records.extend(parse_cloudflare_api(fixtures / "cloudflare-api.json"))
    records.extend(parse_fastly_public_ip_list(fixtures / "fastly-public-ip-list.json"))
    records.extend(parse_github_meta(fixtures / "github-meta.json"))
    records.extend(parse_gitlab_com_docs(fixtures / "gitlab-com.html"))
    records.extend(parse_atlassian_ip_ranges(fixtures / "atlassian-ip-ranges.json"))
    records.extend(parse_stripe_ips(fixtures / "stripe-webhook-ips.json", group="WEBHOOKS", source_label="stripe_webhook_ips_json"))
    records.extend(parse_stripe_ips(fixtures / "stripe-api-ips.json", group="API", source_label="stripe_api_ips_json"))
    return sort_records(records)


def build_from_live_sources(
    *,
    azure_service_tags_url: str,
    aws_url: str = AWS_URL,
    google_cloud_url: str = GOOGLE_CLOUD_URL,
    google_goog_url: str = GOOGLE_GOOG_URL,
    cloudflare_v4_url: str = CLOUDFLARE_V4_URL,
    cloudflare_v6_url: str = CLOUDFLARE_V6_URL,
    oracle_url: str = ORACLE_URL,
    fastly_url: str = FASTLY_URL,
    github_meta_url: str = GITHUB_META_URL,
    gitlab_docs_url: str = GITLAB_DOCS_URL,
    atlassian_url: str = ATLASSIAN_URL,
    stripe_webhooks_url: str = STRIPE_WEBHOOKS_URL,
    stripe_api_url: str = STRIPE_API_URL,
) -> list[EgressRangeRecord]:
    if not azure_service_tags_url:
        raise ValueError("live build requires --azure-service-tags-url")
    records: list[EgressRangeRecord] = []
    records.extend(parse_aws_ip_ranges(aws_url))
    records.extend(parse_google_ranges(google_cloud_url, feed_kind="cloud"))
    records.extend(parse_google_ranges(google_goog_url, feed_kind="goog"))
    records.extend(parse_azure_service_tags(azure_service_tags_url))
    records.extend(parse_oracle_public_ip_ranges(oracle_url))
    records.extend(parse_cloudflare_text(cloudflare_v4_url, source_label="cloudflare_ips_v4"))
    records.extend(parse_cloudflare_text(cloudflare_v6_url, source_label="cloudflare_ips_v6"))
    records.extend(parse_fastly_public_ip_list(fastly_url))
    records.extend(parse_github_meta(github_meta_url))
    records.extend(parse_gitlab_com_docs(gitlab_docs_url))
    records.extend(parse_atlassian_ip_ranges(atlassian_url))
    records.extend(parse_stripe_ips(stripe_webhooks_url, group="WEBHOOKS", source_label="stripe_webhook_ips_json"))
    records.extend(parse_stripe_ips(stripe_api_url, group="API", source_label="stripe_api_ips_json"))
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
    catalog = provider_catalog()
    write_json(output_dir / PROVIDER_CATALOG_JSON, {"generated_at": timestamp, "providers": catalog})
    write_provider_catalog_markdown(output_dir / PROVIDER_CATALOG_MARKDOWN, catalog, data, timestamp)

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
        PROVIDER_CATALOG_JSON: sha256_file(output_dir / PROVIDER_CATALOG_JSON),
        PROVIDER_CATALOG_MARKDOWN: sha256_file(output_dir / PROVIDER_CATALOG_MARKDOWN),
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
        "provider_catalog_coverage": provider_catalog_coverage(data),
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


def provider_catalog_coverage(data: list[dict]) -> dict:
    catalog = provider_catalog()
    ranged = {row["provider"] for row in data}
    statuses = Counter(item["implementation_status"] for item in catalog)
    return {
        "catalog_providers": len(catalog),
        "providers_with_cidr_records": len(ranged),
        "providers_without_cidr_records": len({item["provider"] for item in catalog} - ranged),
        "status_counts": dict(sorted(statuses.items())),
        "cidr_record_providers": sorted(ranged),
        "not_in_cidr_feed": sorted(item["provider"] for item in catalog if item["provider"] not in ranged),
    }


def write_provider_catalog_markdown(path: Path, catalog: list[dict], data: list[dict], timestamp: str) -> None:
    provider_counts = Counter(row["provider"] for row in data)
    lines = [
        "# cloud-egress-ip-ranges provider catalog",
        "",
        f"Generated: `{timestamp}`",
        "",
        "| Tier | Provider | Category | Method | Status | CIDR records | Priority |",
        "|---:|---|---|---|---|---:|---:|",
    ]
    for item in sorted(catalog, key=lambda row: (row["tier"], -row["priority"], row["provider"])):
        lines.append(
            "| {tier} | `{provider}` | {category} | {method} | {status} | {records} | {priority} |".format(
                tier=item["tier"],
                provider=item["provider"],
                category=item["category"],
                method=item["collection_method"],
                status=item["implementation_status"],
                records=provider_counts.get(item["provider"], 0),
                priority=item["priority"],
            )
        )
    coverage = provider_catalog_coverage(data)
    lines.extend(
        [
            "",
            "## Coverage summary",
            "",
            f"- Catalog providers: `{coverage['catalog_providers']}`",
            f"- Providers with CIDR records in this build: `{coverage['providers_with_cidr_records']}`",
            f"- Providers not in the CIDR feed yet: `{coverage['providers_without_cidr_records']}`",
            "",
            "Providers without CIDR records are retained in the catalog because they require docs scraping, ASN/BGP/RDAP enrichment, customer-specific data, or capability-only handling.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
