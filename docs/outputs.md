# Outputs

Builds write root artifacts and classified lists.

## Root Files

- `dist/cloud-egress-ip-ranges.json`: canonical JSON feed with schema version, generation timestamp, and records.
- `dist/cloud-egress-ip-ranges.csv`: tabular feed with one row per CIDR.
- `dist/manifest.json`: counts, source inventory, classified list inventory, and SHA256 checksums.
- `dist/sources.md`: generated provider/feed inventory used as the daily release body.
- `dist/provider-catalog.json`: tiered provider catalog with collection method and implementation status.
- `dist/provider-catalog.md`: human-readable provider coverage report.

## Classified Lists

Each classified list is emitted as JSON and plain text:

- JSON files include classification metadata and full records.
- TXT files contain one CIDR per line for simple allowlist, denylist, WAF, or rate-limit tooling.

Directory layout:

- `dist/classified/provider/<provider>.json`
- `dist/classified/provider/<provider>.txt`
- `dist/classified/platform_family/<family>.json`
- `dist/classified/platform_family/<family>.txt`
- `dist/classified/service_hint/<service>.json`
- `dist/classified/service_hint/<service>.txt`
- `dist/classified/precision_level/<level>.json`
- `dist/classified/precision_level/<level>.txt`
- `dist/classified/recommended_action/<action>.json`
- `dist/classified/recommended_action/<action>.txt`

Examples:

- `dist/classified/provider/cloudflare.txt`
- `dist/classified/platform_family/edge-network.json`
- `dist/classified/precision_level/l2.txt`
- `dist/classified/recommended_action/rate-limit-or-challenge.txt`

Use `manifest.json` to discover the complete inventory, inspect `provider_catalog_coverage`, and verify checksums.
