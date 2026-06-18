from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from .confidence import EXACT_ATTRIBUTION_SOURCE_TYPES, PrecisionLevel

SCHEMA_VERSION = "1.0"


def today_utc() -> str:
    return date.today().isoformat()


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class EgressRangeRecord:
    cidr: str
    provider: str
    platform_family: str
    service_hint: str
    serverless_possible: bool
    serverless_exact: bool
    edge_possible: bool
    region: str | None
    country_hint: str | None
    source: str
    source_type: str
    confidence: int
    recommended_action: str
    false_positive_risk: int
    last_seen: str
    last_updated: str
    precision_level: str = "L1"
    notes: list[str] = field(default_factory=list)
    network_border_group: str | None = None

    def __post_init__(self) -> None:
        self.validate()

    @property
    def network(self) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        return ipaddress.ip_network(self.cidr, strict=False)

    def validate(self) -> None:
        try:
            ipaddress.ip_network(self.cidr, strict=False)
        except ValueError as exc:
            raise ValueError(f"invalid cidr {self.cidr!r}") from exc
        required = {
            "provider": self.provider,
            "platform_family": self.platform_family,
            "service_hint": self.service_hint,
            "source": self.source,
            "source_type": self.source_type,
            "recommended_action": self.recommended_action,
            "last_seen": self.last_seen,
            "last_updated": self.last_updated,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        for field_name, value in {
            "confidence": self.confidence,
            "false_positive_risk": self.false_positive_risk,
        }.items():
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be between 0 and 100")
        if self.serverless_exact and self.source_type not in EXACT_ATTRIBUTION_SOURCE_TYPES:
            raise ValueError(
                "serverless_exact requires owner_confirmed or observed_probe_confirmed source_type"
            )
        if not self.precision_level.startswith("L"):
            raise ValueError("precision_level must be an L0-L5 value")
        level_number = int(self.precision_level[1:])
        if level_number not in {level.value for level in PrecisionLevel}:
            raise ValueError("precision_level must be an L0-L5 value")

    def to_dict(self) -> dict[str, Any]:
        return {
            "cidr": self.cidr,
            "provider": self.provider,
            "platform_family": self.platform_family,
            "service_hint": self.service_hint,
            "serverless_possible": self.serverless_possible,
            "serverless_exact": self.serverless_exact,
            "edge_possible": self.edge_possible,
            "region": self.region,
            "country_hint": self.country_hint,
            "source": self.source,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "recommended_action": self.recommended_action,
            "false_positive_risk": self.false_positive_risk,
            "last_seen": self.last_seen,
            "last_updated": self.last_updated,
            "precision_level": self.precision_level,
            "notes": list(self.notes),
            "network_border_group": self.network_border_group,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EgressRangeRecord":
        return cls(**data)

