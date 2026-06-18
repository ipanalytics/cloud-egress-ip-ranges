from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json, load_text


def parse_cloudflare_text(source: str | Path, *, source_label: str = "cloudflare_ips") -> list[EgressRangeRecord]:
    records: list[EgressRangeRecord] = []
    for line in load_text(source).splitlines():
        cidr = line.strip()
        if cidr and not cidr.startswith("#"):
            records.append(_record(cidr, source_label))
    return records


def parse_cloudflare_api(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    result = data.get("result", data)
    cidrs = result.get("ipv4_cidrs", []) + result.get("ipv6_cidrs", [])
    return [_record(cidr, "cloudflare_api") for cidr in cidrs]


def _record(cidr: str, source_label: str) -> EgressRangeRecord:
    profile = profile_for(
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE,
        provider="cloudflare",
        service_hint="cloudflare_edge",
        serverless_possible=True,
        edge_possible=True,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="cloudflare",
        platform_family="edge_network",
        service_hint="cloudflare_edge",
        serverless_possible=True,
        serverless_exact=False,
        edge_possible=True,
        region="global",
        country_hint=None,
        source=source_label,
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["Cloudflare official range; Workers/CDN/proxy use is possible."],
    )

