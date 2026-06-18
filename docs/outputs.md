# Outputs

Builds write root artifacts and classified lists.

## Root Files

- `dist/cloud-egress-ip-ranges.json`: canonical JSON feed with schema version, generation timestamp, and records.
- `dist/cloud-egress-ip-ranges.csv`: tabular feed with one row per CIDR.
- `dist/cloud-egress-ip-ranges.jsonl`: one JSON record per line.
- `dist/cloud-egress-ip-ranges.parquet`: columnar feed for analytics engines.
- `dist/cloud-egress-ip-ranges.sqlite`: SQLite database with indexed `egress_ranges` table.
- `dist/cloud-egress-ip-ranges.duckdb`: DuckDB database with `egress_ranges` table.
- `dist/manifest.json`: counts, source inventory, classified list inventory, and SHA256 checksums.
- `dist/latest.json`: compact release summary and stable artifact pointers.
- `dist/diff/latest.json`: added/removed range keys relative to a previous feed when provided.
- `dist/sources.md`: generated provider/feed inventory used as the daily release body.
- `dist/providers.yaml`: public provider registry.
- `dist/egress-capabilities.json`: provider capability matrix.
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

## Integration Outputs

- `dist/integrations/nginx/geo.conf`: NGINX `geo` map keyed by CIDR.
- `dist/integrations/cloudflare/ip-list.txt`: plain CIDR list suitable for Cloudflare list imports.
- `dist/integrations/splunk/cloud_egress_lookup.csv`: Splunk lookup CSV.
- `dist/integrations/elastic/bulk.ndjson`: Elasticsearch/OpenSearch bulk NDJSON.
- `dist/integrations/clickhouse/cloud_egress_ip_ranges.sql`: ClickHouse DDL and insert statements.
