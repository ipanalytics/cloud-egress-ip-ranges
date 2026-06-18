from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json, require


def parse_aws_ip_ranges(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    sync_token = require(data, "syncToken", "aws_ip_ranges_json")
    records: list[EgressRangeRecord] = []
    for item in data.get("prefixes", []):
        records.append(_record(item["ip_prefix"], item, sync_token))
    for item in data.get("ipv6_prefixes", []):
        records.append(_record(item["ipv6_prefix"], item, sync_token))
    return records


def _record(cidr: str, item: dict, sync_token: str) -> EgressRangeRecord:
    service = item.get("service", "AMAZON")
    serverless_possible = service in {"AMAZON", "EC2", "API_GATEWAY", "LAMBDA"}
    edge_possible = service in {"CLOUDFRONT", "GLOBALACCELERATOR"}
    level = (
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE
        if service in {"CLOUDFRONT", "API_GATEWAY"}
        else PrecisionLevel.L2_SERVERLESS_POSSIBLE
    )
    profile = profile_for(
        level,
        provider="aws",
        service_hint=service,
        serverless_possible=serverless_possible,
        edge_possible=edge_possible,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="aws",
        platform_family="edge_network" if edge_possible else "cloud",
        service_hint=service,
        serverless_possible=serverless_possible,
        serverless_exact=False,
        edge_possible=edge_possible,
        region=item.get("region"),
        country_hint=None,
        source="aws_ip_ranges_json",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=[f"AWS sync token {sync_token}; exact Lambda attribution is not public."],
        network_border_group=item.get("network_border_group"),
    )

