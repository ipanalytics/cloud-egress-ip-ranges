from __future__ import annotations

from .lookup import LookupResult


def explain_lookup(result: LookupResult) -> str:
    if not result.matches:
        return f"{result.ip}: no matching cloud egress range in the loaded feed."
    lines = [f"{result.ip}: {len(result.matches)} matching range(s)"]
    for record in result.matches:
        possible = []
        if record.serverless_possible:
            possible.append("serverless possible")
        if record.edge_possible:
            possible.append("edge possible")
        possible_text = ", ".join(possible) if possible else "cloud/provider range"
        exact_text = (
            "exact serverless attribution is confirmed"
            if record.serverless_exact
            else "exact serverless attribution is not claimed from this source"
        )
        lines.append(
            "- {cidr} provider={provider} service={service} confidence={confidence} "
            "false_positive_risk={risk} action={action}; {possible}; {exact}. Source: {source} ({source_type}).".format(
                cidr=record.cidr,
                provider=record.provider,
                service=record.service_hint,
                confidence=record.confidence,
                risk=record.false_positive_risk,
                action=record.recommended_action,
                possible=possible_text,
                exact=exact_text,
                source=record.source,
                source_type=record.source_type,
            )
        )
    return "\n".join(lines)

