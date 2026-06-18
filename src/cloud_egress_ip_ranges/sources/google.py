from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json, require


def parse_google_ranges(source: str | Path, *, feed_kind: str) -> list[EgressRangeRecord]:
    data = load_json(source)
    require(data, "prefixes", f"google_{feed_kind}_json")
    records: list[EgressRangeRecord] = []
    for item in data["prefixes"]:
        cidr = item.get("ipv4Prefix") or item.get("ipv6Prefix")
        if not cidr:
            raise ValueError(f"google_{feed_kind}_json: prefix missing ipv4Prefix/ipv6Prefix")
        records.append(_record(cidr, item, feed_kind))
    return records


def _record(cidr: str, item: dict, feed_kind: str) -> EgressRangeRecord:
    is_cloud = feed_kind == "cloud"
    service_hint = "gcp_customer_external_ip" if is_cloud else "google_owned_ip"
    level = PrecisionLevel.L2_SERVERLESS_POSSIBLE if is_cloud else PrecisionLevel.L1_OFFICIAL_PROVIDER_RANGE
    profile = profile_for(
        level,
        provider="google_cloud",
        service_hint=service_hint,
        serverless_possible=is_cloud,
        edge_possible=False,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="google_cloud" if is_cloud else "google",
        platform_family="cloud" if is_cloud else "provider_network",
        service_hint=service_hint,
        serverless_possible=is_cloud,
        serverless_exact=False,
        edge_possible=False,
        region=item.get("scope"),
        country_hint=None,
        source=f"google_{feed_kind}_json",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["Google cloud.json customer resource range." if is_cloud else "Google-owned range from goog.json."],
    )

