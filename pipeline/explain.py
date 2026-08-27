from pipeline.evidence import Evidence


TEMPLATES = {
    "R1_COST_DEVIATION": "Cost is {cost:.1f} L against a peer median of {peer_median:.1f} L for {n} comparable works in {group} (robust z = {z_score:.1f})",
    "R2_PROGRESS_MISMATCH": "{utilisation_pct:.0f}% of funds released against {progress_pct:.0f}% reported physical progress - a {gap_pp:.0f} percentage point gap",
    "R3_DELAY": "{days_overdue} days past the category median completion window (overrun ratio {overrun_ratio:.1f}x)",
    "R4_PAYMENT_PATTERN": "Payment pattern flags: {n_payments} payments, max single = {max_pct:.0f}% of total, {before_50_pct:.0f}% released before 50% progress",
    "R5_UTILISATION": "Utilisation ratio is {utilisation_ratio:.2f} - {description}",
    "R6_COMPLIANCE": "Missing or inconsistent: {missing_elements}",
    "IF_ANOMALY": "Isolation Forest ranks this in the top {anomaly_percentile:.0f}% for unusual feature combination ({features})",
    "DUP_OVERLAP": "{similarity:.2f} description similarity to {matched_project}, same district, sanctioned {day_gap} days apart",
}


def generate_explanation(evidence_list: list[Evidence], tier: str) -> dict:
    """Generate human-readable explanation from evidence list."""
    if not evidence_list:
        return {
            "summary": "No risk indicators detected. Cost, timing and payments are consistent with comparable works.",
            "reasons": [],
            "action": "No action required",
            "confidence": "high",
        }

    sorted_evidence = sorted(evidence_list, key=lambda e: -e.points)
    reasons = []
    for e in sorted_evidence[:5]:
        reason = _format_reason(e)
        reasons.append(reason)

    if len(sorted_evidence) >= 3:
        summary = "Multiple independent risk indicators converge on this project."
        dims = set(e.dimension for e in sorted_evidence)
        if len(dims) >= 3:
            summary += f" Signals span {len(dims)} risk dimensions."
    elif len(sorted_evidence) == 2:
        summary = f"{sorted_evidence[0].headline}. Additionally, {sorted_evidence[1].headline.lower()}."
    else:
        summary = sorted_evidence[0].headline + "."

    action = _determine_action(tier)
    confidence = _min_confidence(sorted_evidence)

    return {
        "summary": summary,
        "reasons": reasons,
        "action": action,
        "confidence": confidence,
    }


def _format_reason(e: Evidence) -> str:
    """Format an evidence item into a readable sentence."""
    if e.detail:
        return e.detail

    template = TEMPLATES.get(e.code)
    if not template:
        return e.headline

    try:
        feats = e.features.copy()
        ctx = e.peer_context.copy()

        if e.code == "R1_COST_DEVIATION":
            feats.setdefault("n", ctx.get("n", "?"))
            feats.setdefault("group", ctx.get("group", "comparable works"))
        elif e.code == "R4_PAYMENT_PATTERN":
            feats["max_pct"] = feats.get("max_payment_share", 0) * 100
            feats["before_50_pct"] = feats.get("pct_before_50", 0) * 100
        elif e.code == "R5_UTILISATION":
            ratio = feats.get("utilisation_ratio", 0)
            if ratio > 1:
                feats["description"] = f"expenditure exceeds the sanctioned amount by {(ratio-1)*100:.0f}%"
            else:
                feats["description"] = f"only {ratio*100:.0f}% of sanctioned funds utilised despite completion"
        elif e.code == "R6_COMPLIANCE":
            elements = feats.get("missing_elements", [])
            feats["missing_elements"] = ", ".join(elements) if isinstance(elements, list) else str(elements)
        elif e.code == "IF_ANOMALY":
            top = feats.get("top_features", [])
            feats["features"] = ", ".join(top) if isinstance(top, list) else str(top)
        elif e.code == "DUP_OVERLAP":
            feats.update(ctx)

        return template.format(**feats)
    except (KeyError, TypeError):
        return e.headline


def _determine_action(tier: str) -> str:
    actions = {
        "CRITICAL": "Priority field verification by District Authority",
        "HIGH": "Recommended for desk review before next instalment",
        "MEDIUM": "Watch list; re-check at next reporting cycle",
        "LOW": "No action required",
    }
    return actions.get(tier, "No action required")


def _min_confidence(evidence_list: list[Evidence]) -> str:
    levels = {"high": 3, "medium": 2, "low": 1}
    if not evidence_list:
        return "low"
    min_level = min(levels.get(e.confidence, 2) for e in evidence_list)
    return {3: "high", 2: "medium", 1: "low"}.get(min_level, "medium")
