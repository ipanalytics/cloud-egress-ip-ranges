from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json, require


def parse_oracle_public_ip_ranges(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    require(data, "regions", "oracle_public_ip_ranges_json")
    records: list[EgressRangeRecord] = []
    for region in data["regions"]:
        region_name = region.get("region")
        for item in region.get("cidrs", []):
            cidr = item.get("cidr")
            tags = item.get("tags", ["OCI"])
            if not cidr:
                raise ValueError("oracle_public_ip_ranges_json: missing cidr")
            records.append(_record(cidr, region_name, tags))
    return records


def _record(cidr: str, region: str | None, tags: list[str]) -> EgressRangeRecord:
    service_hint = "+".join(sorted(tags)) if tags else "OCI"
    serverless_possible = "OCI" in tags or "OSN" in tags
    profile = profile_for(
        PrecisionLevel.L2_SERVERLESS_POSSIBLE,
        provider="oracle_cloud",
        service_hint=service_hint,
        serverless_possible=serverless_possible,
        edge_possible=False,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="oracle_cloud",
        platform_family="cloud",
        service_hint=service_hint,
        serverless_possible=serverless_possible,
        serverless_exact=False,
        edge_possible=False,
        region=region,
        country_hint=None,
        source="oracle_public_ip_ranges_json",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["Oracle OCI public IP range; exact Oracle Functions attribution is not public."],
    )

