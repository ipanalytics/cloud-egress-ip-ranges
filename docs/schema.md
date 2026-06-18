# Schema

Every emitted range is a JSON object with stable keys. The core fields are:

- `cidr`: IPv4 or IPv6 CIDR.
- `provider`: normalized provider slug such as `aws`, `google_cloud`, `azure`, or `cloudflare`.
- `platform_family`: broad family such as `cloud`, `edge_network`, or `serverless_platform`.
- `service_hint`: provider service label or conservative project label.
- `serverless_possible`: true when serverless or managed compute can plausibly use the range.
- `serverless_exact`: true only for owner-confirmed or observed-probe-confirmed egress.
- `edge_possible`: true when edge/CDN/proxy egress is plausible.
- `source`: feed or metadata source identifier.
- `source_type`: `official_feed`, `owner_confirmed`, `observed_probe_confirmed`, or `metadata_only`.
- `confidence`: integer 0 through 100.
- `false_positive_risk`: integer 0 through 100.
- `recommended_action`: `allow`, `monitor`, `rate_limit_or_challenge`, or `challenge`.
- `precision_level`: `L0` through `L5`.
- `last_seen` and `last_updated`: ISO dates.

## Precision Levels

- `L0`: exact official service range, for example a provider-published CloudFront or Cloudflare range.
- `L1`: official provider range, for example AWS `AMAZON` or Google Cloud customer external IP ranges.
- `L2`: serverless possible, where public feed data cannot prove exact serverless origin.
- `L3`: owner-confirmed egress, supplied by the service owner or tenant.
- `L4`: observed probe-confirmed egress, measured by a controlled probe.
- `L5`: weak inference from ASN, RDAP, WHOIS, or similar indirect evidence.

## AWS Example

```json
{
  "cidr": "3.5.140.0/22",
  "provider": "aws",
  "platform_family": "cloud",
  "service_hint": "AMAZON",
  "serverless_possible": true,
  "serverless_exact": false,
  "edge_possible": false,
  "region": "ap-northeast-2",
  "country_hint": null,
  "source": "aws_ip_ranges_json",
  "source_type": "official_feed",
  "confidence": 70,
  "recommended_action": "rate_limit_or_challenge",
  "false_positive_risk": 50,
  "last_seen": "2026-06-18",
  "last_updated": "2026-06-18",
  "precision_level": "L2",
  "notes": ["AWS official range; exact Lambda attribution is not public."],
  "network_border_group": "ap-northeast-2"
}
```

## Cloudflare Example

```json
{
  "cidr": "1.1.1.0/24",
  "provider": "cloudflare",
  "platform_family": "edge_network",
  "service_hint": "cloudflare_edge",
  "serverless_possible": true,
  "serverless_exact": false,
  "edge_possible": true,
  "region": "global",
  "country_hint": null,
  "source": "cloudflare_ips",
  "source_type": "official_feed",
  "confidence": 91,
  "recommended_action": "challenge",
  "false_positive_risk": 29,
  "last_seen": "2026-06-18",
  "last_updated": "2026-06-18",
  "precision_level": "L0",
  "notes": ["Cloudflare official edge range; Workers/CDN/proxy use is possible."],
  "network_border_group": null
}
```

