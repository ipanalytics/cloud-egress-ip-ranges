from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from .feed import Feed
from .models import EgressRangeRecord


@dataclass(frozen=True)
class LookupResult:
    ip: str
    matches: tuple[EgressRangeRecord, ...]

    def to_dict(self) -> dict:
        return {"ip": self.ip, "matches": [record.to_dict() for record in self.matches]}


def lookup_ip(feed: Feed, ip: str) -> LookupResult:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError as exc:
        raise ValueError(f"invalid IP address: {ip}") from exc
    matches = [
        record
        for record in feed.records
        if record.network.version == address.version and address in record.network
    ]
    matches.sort(key=lambda record: (-record.network.prefixlen, -record.confidence, record.provider, record.cidr))
    return LookupResult(ip=str(address), matches=tuple(matches))

