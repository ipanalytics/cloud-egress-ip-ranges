from __future__ import annotations

import ipaddress
from pathlib import Path

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord, today_utc
from cloud_egress_ip_ranges.sources.common import load_json


def parse_stripe_ips(source: str | Path, *, group: str, source_label: str) -> list[EgressRangeRecord]:
    data = load_json(source)
    cidrs = data.get(group, [])
    if not cidrs:
        raise ValueError(f"{source_label}: missing {group}")
    return [_record(normalize_ip_or_cidr(value), group.lower(), source_label) for value in cidrs]


def normalize_ip_or_cidr(value: str) -> str:
    if "/" in value:
        return value
    address = ipaddress.ip_address(value)
    return f"{address}/32" if address.version == 4 else f"{address}/128"


def _record(cidr: str, group: str, source_label: str) -> EgressRangeRecord:
    service_hint = f"stripe_{group}"
    profile = profile_for(
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE,
        provider="stripe",
        service_hint=service_hint,
        serverless_possible=False,
        edge_possible=False,
    )
    return EgressRangeRecord(
        cidr=cidr,
        provider="stripe",
        platform_family="webhook_automation" if group == "webhooks" else "payments_api",
        service_hint=service_hint,
        serverless_possible=False,
        serverless_exact=False,
        edge_possible=False,
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
        notes=["Stripe official IP list for outbound platform traffic."],
    )
