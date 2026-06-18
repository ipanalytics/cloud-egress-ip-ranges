# Confidence Model

The feed is designed for risk-aware classification, not absolute attribution.

## Precision Levels

- `L0`: exact official service range. Example: a provider-published edge or service-specific range.
- `L1`: official provider range. Example: a broad AWS, Google, or Azure range.
- `L2`: serverless possible. Example: cloud customer resource ranges where managed compute can egress.
- `L3`: owner-confirmed egress. Example: a tenant publishes its Vercel static egress IPs.
- `L4`: observed probe-confirmed egress. Example: a controlled probe observes a platform request egressing from a CIDR.
- `L5`: weak inference. Example: ASN/RDAP/WHOIS suggests cloud infrastructure but no official feed maps it.

## Scores

- `confidence`: how strongly the record supports provider/platform classification.
- `false_positive_risk`: how likely it is that treating the range as disposable/serverless/edge infrastructure will affect ordinary or unrelated traffic.
- `recommended_action`: one of `allow`, `monitor`, `rate_limit_or_challenge`, or `challenge`.

High confidence does not mean exact workload attribution. For example, Cloudflare official ranges can be high-confidence edge network ranges while still not proving whether the request came from Workers, CDN, proxy, or another Cloudflare product.

## Exact Attribution Guard

`serverless_exact=true` is only valid when `source_type` is `owner_confirmed` or `observed_probe_confirmed`. The model rejects exact claims from broad official feeds.
