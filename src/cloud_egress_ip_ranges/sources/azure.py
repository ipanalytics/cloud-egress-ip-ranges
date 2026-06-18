from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json, require


def parse_azure_service_tags(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    require(data, "values", "azure_service_tags")
    records: list[EgressRangeRecord] = []
    for value in data["values"]:
        properties = value.get("properties", {})
        tag_name = value.get("name", "AzureCloud")
        region = properties.get("region") or value.get("id")
        prefixes = properties.get("addressPrefixes")
        if prefixes is None:
            raise ValueError("azure_service_tags: missing addressPrefixes")
        for cidr in prefixes:
            records.append(_record(cidr, tag_name, region))
    return records


def _record(cidr: str, tag_name: str, region: str | None) -> EgressRangeRecord:
    serverless_possible = tag_name.startswith(("AzureCloud", "AppService", "AzureFrontDoor"))
    edge_possible = tag_name.startswith(("AzureFrontDoor", "AzureTrafficManager"))
    level = PrecisionLevel.L2_SERVERLESS_POSSIBLE if serverless_possible else PrecisionLevel.L1_OFFICIAL_PROVIDER_RANGE
    profile = profile_for(
        level,
        provider="azure",
        service_hint=tag_name,
        serverless_possible=serverless_possible,
        edge_possible=edge_possible,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="azure",
        platform_family="edge_network" if edge_possible else "cloud",
        service_hint=tag_name,
        serverless_possible=serverless_possible,
        serverless_exact=False,
        edge_possible=edge_possible,
        region=region,
        country_hint=None,
        source="azure_service_tags_public_json",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["Azure Service Tags range; exact Azure Functions attribution requires app-owner data."],
    )

