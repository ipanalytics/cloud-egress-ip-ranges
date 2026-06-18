# Sources

The project uses official feeds as the default trust boundary.

## AWS

- Feed: `https://ip-ranges.amazonaws.com/ip-ranges.json`
- Source ID: `aws_ip_ranges_json`
- Useful fields: `ip_prefix`, `ipv6_prefix`, `region`, `service`, `network_border_group`

AWS ranges can show that traffic is from AWS address space or a published AWS service range. Public data does not prove exact Lambda origin for generic `AMAZON` or `EC2` ranges.

## Google

- Google-owned ranges: `https://www.gstatic.com/ipranges/goog.json`
- Google Cloud customer ranges: `https://www.gstatic.com/ipranges/cloud.json`
- Source IDs: `google_goog_json`, `google_cloud_json`
- Useful fields: `ipv4Prefix`, `ipv6Prefix`, `scope`

`cloud.json` is treated as customer Google Cloud resource space. Cloud Run or Cloud Functions can use configured VPC/NAT egress, so public ranges are classified as possible rather than exact.

## Azure

- Feed: Azure IP Ranges and Service Tags, Public Cloud JSON from Microsoft Download Center
- Source ID: `azure_service_tags_public_json`
- Useful fields: service tag `name`, `properties.region`, `properties.addressPrefixes`

Azure Service Tags identify Azure service and regional ranges. Exact Azure Functions attribution still requires app-owner data such as a specific Function App outbound IP list.

## Cloudflare

- IPv4 list: `https://www.cloudflare.com/ips-v4`
- IPv6 list: `https://www.cloudflare.com/ips-v6`
- Source ID: `cloudflare_ips`

Cloudflare ranges are official edge network ranges. Workers, CDN, proxy, WAF, and other edge products can use the network, so the feed marks edge/serverless as possible without claiming a specific product origin.

## Vercel And Netlify

Vercel and Netlify are represented as platform metadata in code and docs. The generated range feed does not emit fake CIDRs for them. Owner-confirmed static egress or probe-confirmed data can be added later with `owner_confirmed` or `observed_probe_confirmed` source types.

