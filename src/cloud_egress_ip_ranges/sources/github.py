from __future__ import annotations

from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json

GITHUB_GROUPS = {
    "actions": ("github_actions", "ci_cd"),
    "hooks": ("github_hooks", "webhook_automation"),
    "pages": ("github_pages", "static_hosting"),
    "api": ("github_api", "dev_platform"),
    "git": ("github_git", "dev_platform"),
    "web": ("github_web", "dev_platform"),
}


def parse_github_meta(source: str | Path) -> list[EgressRangeRecord]:
    data = load_json(source)
    records: list[EgressRangeRecord] = []
    for group, (service_hint, family) in GITHUB_GROUPS.items():
        for cidr in data.get(group, []):
            records.append(_record(cidr, service_hint, family))
    if not records:
        raise ValueError("github_meta_api: no supported CIDR groups found")
    return records


def _record(cidr: str, service_hint: str, family: str) -> EgressRangeRecord:
    profile = profile_for(
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE,
        provider="github",
        service_hint=service_hint,
        serverless_possible=service_hint == "github_actions",
        edge_possible=False,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="github",
        platform_family=family,
        service_hint=service_hint,
        serverless_possible=service_hint == "github_actions",
        serverless_exact=False,
        edge_possible=False,
        region="global",
        country_hint=None,
        source="github_meta_api",
        source_type="official_feed",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["GitHub Meta API range for service-specific GitHub infrastructure."],
    )

