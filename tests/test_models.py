from __future__ import annotations

import unittest

from cloud_egress_ip_ranges.confidence import PrecisionLevel, profile_for
from cloud_egress_ip_ranges.models import EgressRangeRecord


def sample_record(**overrides: object) -> EgressRangeRecord:
    data = {
        "cidr": "34.141.0.0/16",
        "provider": "google_cloud",
        "platform_family": "cloud",
        "service_hint": "gcp_customer_external_ip",
        "serverless_possible": True,
        "serverless_exact": False,
        "edge_possible": False,
        "region": "europe-west3",
        "country_hint": "DE",
        "source": "google_cloud_cloud_json",
        "source_type": "official_feed",
        "confidence": 78,
        "recommended_action": "rate_limit_or_challenge",
        "false_positive_risk": 72,
        "last_seen": "2026-06-18",
        "last_updated": "2026-06-18",
        "precision_level": "L2",
        "notes": ["Google Cloud customer external IP range."],
        "network_border_group": None,
    }
    data.update(overrides)
    return EgressRangeRecord(**data)


class ModelTests(unittest.TestCase):
    def test_serializes_expected_shape(self) -> None:
        record = sample_record()
        serialized = record.to_dict()
        self.assertEqual(serialized["cidr"], "34.141.0.0/16")
        self.assertEqual(serialized["provider"], "google_cloud")
        self.assertTrue(serialized["serverless_possible"])
        self.assertFalse(serialized["serverless_exact"])
        self.assertIn("source_type", serialized)
        self.assertIn("false_positive_risk", serialized)

    def test_round_trip(self) -> None:
        record = sample_record()
        self.assertEqual(EgressRangeRecord.from_dict(record.to_dict()), record)

    def test_rejects_bad_cidr(self) -> None:
        with self.assertRaises(ValueError):
            sample_record(cidr="not-a-cidr")

    def test_rejects_missing_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            sample_record(provider="")

    def test_rejects_score_bounds(self) -> None:
        with self.assertRaises(ValueError):
            sample_record(confidence=101)
        with self.assertRaises(ValueError):
            sample_record(false_positive_risk=-1)

    def test_rejects_exact_claim_from_official_feed(self) -> None:
        with self.assertRaises(ValueError):
            sample_record(serverless_exact=True, source_type="official_feed")

    def test_allows_exact_claim_from_confirmed_source(self) -> None:
        record = sample_record(serverless_exact=True, source_type="owner_confirmed")
        self.assertTrue(record.serverless_exact)

    def test_confidence_profile(self) -> None:
        profile = profile_for(
            PrecisionLevel.L2_SERVERLESS_POSSIBLE,
            provider="aws",
            service_hint="AMAZON",
            serverless_possible=True,
            edge_possible=False,
        )
        self.assertGreaterEqual(profile.confidence, 0)
        self.assertLessEqual(profile.confidence, 100)
        self.assertIn(profile.recommended_action, {"allow", "monitor", "rate_limit_or_challenge", "challenge"})


if __name__ == "__main__":
    unittest.main()

