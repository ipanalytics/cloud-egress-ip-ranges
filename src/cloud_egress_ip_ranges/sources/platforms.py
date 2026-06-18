from __future__ import annotations

PLATFORM_METADATA = [
    {
        "provider": "vercel",
        "platform_family": "serverless_platform",
        "service_hint": "vercel_functions",
        "public_ranges_available": False,
        "static_egress_supported": True,
        "notes": "Vercel supports static egress IPs, but no exhaustive public function egress range is emitted here.",
    },
    {
        "provider": "netlify",
        "platform_family": "serverless_platform",
        "service_hint": "netlify_functions",
        "public_ranges_available": False,
        "static_egress_supported": True,
        "notes": "Netlify private connectivity can provide allowlistable egress, but default dynamic function egress is not emitted here.",
    },
]


def platform_metadata() -> list[dict]:
    return [dict(item) for item in PLATFORM_METADATA]

