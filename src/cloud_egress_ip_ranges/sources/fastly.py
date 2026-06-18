from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json


def parse_fastly_public_ip_list(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    cidrs = data.get("addresses", []) + data.get("ipv6_addresses", [])
    if not cidrs:
        raise ValueError("fastly_public_ip_list: missing addresses")
    return [_record(cidr) for cidr in cidrs]


def _record(cidr: str) -> EgressRangeRecord:
    profile = profile_for(
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE,
        provider="fastly",
        service_hint="fastly_edge",
        serverless_possible=True,
        edge_possible=True,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="fastly",
        platform_family="edge_network",
        service_hint="fastly_edge",
        serverless_possible=True,
        serverless_exact=False,
        edge_possible=True,
        region="global",
        country_hint=None,
        source="fastly_public_ip_list",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["Fastly official public IP list; CDN and Compute use is possible."],
    )

