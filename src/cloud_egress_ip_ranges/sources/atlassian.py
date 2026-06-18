from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json


def parse_atlassian_ip_ranges(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    records: list[EgressRangeRecord] = []
    for item in data.get("items", []):
        if "egress" not in item.get("direction", []):
            continue
        cidr = item.get("cidr")
        products = item.get("product", [])
        if cidr:
            records.append(_record(cidr, products, item.get("region", [])))
    if not records:
        raise ValueError("atlassian_ip_ranges_json: no egress CIDRs found")
    return records


def _service_hint(products: list[str]) -> str:
    if len(products) == 1:
        return f"atlassian_{products[0].replace('-', '_')}"
    if "bitbucket" in products:
        return "atlassian_bitbucket"
    return "atlassian_cloud"


def _record(cidr: str, products: list[str], regions: list[str]) -> EgressRangeRecord:
    service_hint = _service_hint(products)
    profile = profile_for(
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE,
        provider="atlassian",
        service_hint=service_hint,
        serverless_possible=service_hint == "atlassian_bitbucket",
        edge_possible=False,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="atlassian",
        platform_family="dev_platform",
        service_hint=service_hint,
        serverless_possible=service_hint == "atlassian_bitbucket",
        serverless_exact=False,
        edge_possible=False,
        region=",".join(regions) if regions else "global",
        country_hint=None,
        source="atlassian_ip_ranges_json",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["Atlassian official IP range with egress direction."],
    )
