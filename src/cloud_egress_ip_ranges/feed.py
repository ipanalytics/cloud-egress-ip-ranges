from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .models import EgressRangeRecord


@dataclass(frozen=True)
class Feed:
    schema_version: str
    generated_at: str
    records: tuple[EgressRangeRecord, ...]

    @property
    def provider_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(record.provider for record in self.records).items()))

    @property
    def source_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(record.source for record in self.records).items()))

    @property
    def service_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(record.service_hint for record in self.records).items()))


def load_feed(path: str | Path = "dist/cloud-egress-ip-ranges.json") -> Feed:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = tuple(EgressRangeRecord.from_dict(item) for item in payload["records"])
    return Feed(
        schema_version=payload["schema_version"],
        generated_at=payload["generated_at"],
        records=records,
    )

