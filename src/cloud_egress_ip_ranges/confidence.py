from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class PrecisionLevel(IntEnum):
    L0_EXACT_OFFICIAL_SERVICE_RANGE = 0
    L1_OFFICIAL_PROVIDER_RANGE = 1
    L2_SERVERLESS_POSSIBLE = 2
    L3_OWNER_CONFIRMED_EGRESS = 3
    L4_OBSERVED_PROBE_CONFIRMED = 4
    L5_WEAK_INFERENCE = 5


PRECISION_DESCRIPTIONS: dict[PrecisionLevel, str] = {
    PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE: "Exact official service range.",
    PrecisionLevel.L1_OFFICIAL_PROVIDER_RANGE: "Official cloud or provider range.",
    PrecisionLevel.L2_SERVERLESS_POSSIBLE: "Serverless or managed compute is possible.",
    PrecisionLevel.L3_OWNER_CONFIRMED_EGRESS: "Owner-confirmed egress range.",
    PrecisionLevel.L4_OBSERVED_PROBE_CONFIRMED: "Observed probe-confirmed egress.",
    PrecisionLevel.L5_WEAK_INFERENCE: "Weak ASN, RDAP, or WHOIS inference.",
}

EXACT_ATTRIBUTION_SOURCE_TYPES = {"owner_confirmed", "observed_probe_confirmed"}


@dataclass(frozen=True)
class ConfidenceProfile:
    precision_level: PrecisionLevel
    confidence: int
    false_positive_risk: int
    recommended_action: str


def recommended_action(confidence: int, false_positive_risk: int) -> str:
    if confidence >= 85 and false_positive_risk <= 35:
        return "challenge"
    if confidence >= 65:
        return "rate_limit_or_challenge"
    if confidence >= 45:
        return "monitor"
    return "allow"


def profile_for(
    precision_level: PrecisionLevel,
    *,
    provider: str,
    service_hint: str,
    serverless_possible: bool,
    edge_possible: bool,
) -> ConfidenceProfile:
    base = {
        PrecisionLevel.L0_EXACT_OFFICIAL_SERVICE_RANGE: 88,
        PrecisionLevel.L1_OFFICIAL_PROVIDER_RANGE: 74,
        PrecisionLevel.L2_SERVERLESS_POSSIBLE: 68,
        PrecisionLevel.L3_OWNER_CONFIRMED_EGRESS: 92,
        PrecisionLevel.L4_OBSERVED_PROBE_CONFIRMED: 90,
        PrecisionLevel.L5_WEAK_INFERENCE: 42,
    }[precision_level]
    if provider in {"cloudflare", "fastly"} and edge_possible:
        base += 3
    if service_hint in {"AMAZON", "EC2", "AzureCloud", "gcp_customer_external_ip"}:
        base -= 4
    if serverless_possible:
        false_positive_risk = max(25, 100 - base + 20)
    elif edge_possible:
        false_positive_risk = max(20, 100 - base + 10)
    else:
        false_positive_risk = max(15, 100 - base)
    confidence = max(0, min(100, base))
    false_positive_risk = max(0, min(100, false_positive_risk))
    return ConfidenceProfile(
        precision_level=precision_level,
        confidence=confidence,
        false_positive_risk=false_positive_risk,
        recommended_action=recommended_action(confidence, false_positive_risk),
    )

