from __future__ import annotations

from pathlib import Path
import re

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_text

CIDR_RE = re.compile(r"\b[0-9]+(?:\.[0-9]+){3}/[0-9]+\b")


def parse_gitlab_com_docs(source: str | Path) -> list[EgressRangeRecord]:
    text = load_text(source)
    cidrs = sorted(set(CIDR_RE.findall(text)))
    if not cidrs:
        raise ValueError("gitlab_com_docs: no documented GitLab.com CIDRs found")
    return [_record(cidr) for cidr in cidrs]


def _record(cidr: str) -> EgressRangeRecord:
    profile = profile_for(
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE,
        provider="gitlab",
        service_hint="gitlab_web_api_webhooks",
        serverless_possible=False,
        edge_possible=False,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="gitlab",
        platform_family="dev_platform",
        service_hint="gitlab_web_api_webhooks",
        serverless_possible=False,
        serverless_exact=False,
        edge_possible=False,
        region="global",
        country_hint=None,
        source="gitlab_com_docs",
        source_type="official_docs",
        confidence=profile.confidence,
        recommended_action=profile.recommended_action,
        false_positive_risk=profile.false_positive_risk,
        last_seen=today_utc(),
        last_updated=today_utc(),
        precision_level=f"L{profile.precision_level.value}",
        notes=["GitLab.com documented Web/API and webhook source range; SaaS runner egress is not static."],
    )

