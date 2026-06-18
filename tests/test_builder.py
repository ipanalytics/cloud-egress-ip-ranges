from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from cloud_egress_ip_ranges.builder import ROOT_CSV, ROOT_JSON, SOURCES_MARKDOWN, build_from_fixtures, write_artifacts
from cloud_egress_ip_ranges.sources.aws import parse_aws_ip_ranges


class BuilderTests(unittest.TestCase):
    def test_build_writes_root_and_classified_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            manifest = write_artifacts(build_from_fixtures(), output, offline=True)
            self.assertTrue((output / ROOT_JSON).exists())
            self.assertTrue((output / ROOT_CSV).exists())
            self.assertTrue((output / "manifest.json").exists())
            self.assertTrue((output / SOURCES_MARKDOWN).exists())
            self.assertTrue((output / "classified" / "provider" / "aws.json").exists())
            self.assertGreater(manifest["total_records"], 0)
            self.assertGreater(len(manifest["classified"]), 0)
            self.assertGreater(len(manifest["source_catalog"]), 0)

    def test_json_and_csv_counts_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            write_artifacts(build_from_fixtures(), output, offline=True)
            payload = json.loads((output / ROOT_JSON).read_text(encoding="utf-8"))
            with (output / ROOT_CSV).open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(payload["records"]), len(rows))

    def test_offline_build_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            write_artifacts(build_from_fixtures(), Path(left), offline=True)
            write_artifacts(build_from_fixtures(), Path(right), offline=True)
            self.assertEqual((Path(left) / ROOT_JSON).read_bytes(), (Path(right) / ROOT_JSON).read_bytes())
            self.assertEqual((Path(left) / ROOT_CSV).read_bytes(), (Path(right) / ROOT_CSV).read_bytes())

    def test_classified_files_match_classification(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            write_artifacts(build_from_fixtures(), output, offline=True)
            provider_payload = json.loads(
                (output / "classified" / "provider" / "cloudflare.json").read_text(encoding="utf-8")
            )
            self.assertEqual(provider_payload["classification"], {"kind": "provider", "value": "cloudflare"})
            self.assertTrue(all(row["provider"] == "cloudflare" for row in provider_payload["records"]))

    def test_malformed_fixture_failure_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "bad-aws.json"
            bad.write_text('{"prefixes": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "aws_ip_ranges_json"):
                parse_aws_ip_ranges(bad)

    def test_sources_markdown_contains_provider_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            write_artifacts(build_from_fixtures(), output, offline=True)
            text = (output / SOURCES_MARKDOWN).read_text(encoding="utf-8")
            self.assertIn("AWS ip-ranges.json", text)
            self.assertIn("Google Cloud cloud.json", text)
            self.assertIn("Azure Public Service Tags JSON", text)
            self.assertIn("Cloudflare IPv4 ranges", text)


if __name__ == "__main__":
    unittest.main()
