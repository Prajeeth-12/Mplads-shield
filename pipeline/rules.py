import yaml
import os
from typing import Optional
from pipeline.evidence import Evidence

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

RULES_CFG = CONFIG["rules"]


def check_r1_cost_deviation(row: dict) -> Optional[Evidence]:
    """R1: Cost overrun vs peers using robust z-score."""
    z = row.get("cost_z_score", 0)
    if z is None or z < 2.0:
        return None

    thresholds = RULES_CFG["r1_cost_deviation"]["z_thresholds"]
    points = 0
    for threshold, pts in thresholds:
        if z >= threshold:
            points = pts

    if points == 0:
        return None

    cost = row.get("sanctioned_amount", 0)
    peer_median = row.get("peer_median_cost", 0)
    ratio = round(cost / peer_median, 1) if peer_median > 0 else 0
    peer_n = row.get("peer_group_n", 0)
    peer_group = row.get("peer_group_key", "unknown")

    return Evidence(
        code="R1_COST_DEVIATION",
        dimension="financial",
        points=points,
        headline=f"Cost {ratio}x higher than comparable works",
        detail=f"Cost is {cost:.1f} L against a peer median of {peer_median:.1f} L for {peer_n} comparable works ({peer_group}, robust z = {z:.1f})",
        features={"cost": cost, "peer_median": peer_median, "z_score": round(z, 2), "ratio": ratio},
        peer_context={"group": peer_group, "n": peer_n, "median": peer_median},
        confidence="high" if peer_n >= 50 else "medium",
    )


def check_r2_progress_mismatch(row: dict) -> Optional[Evidence]:
    """R2: Progress-expenditure mismatch (money ahead of work)."""
    util = row.get("utilisation_ratio", 0)
    progress = row.get("progress_pct", 0)

    if util is None or progress is None:
        return None

    util_pct = util * 100 if util <= 1.5 else util
    gap = util_pct - progress

    if gap < 25:
        return None

    thresholds = RULES_CFG["r2_progress_mismatch"]["gap_thresholds"]
    points = 0
    for threshold, pts in thresholds:
        if gap >= threshold:
            points = pts

    if points == 0:
        return None

    return Evidence(
        code="R2_PROGRESS_MISMATCH",
        dimension="progress",
        points=points,
        headline=f"{util_pct:.0f}% funds released against {progress:.0f}% physical progress",
        detail=f"{util_pct:.0f}% of funds released against {progress:.0f}% reported physical progress - a {gap:.0f} percentage point gap",
        features={"utilisation_pct": round(util_pct, 1), "progress_pct": round(progress, 1), "gap_pp": round(gap, 1)},
        peer_context={},
        confidence="high",
    )


def check_r3_delay(row: dict) -> Optional[Evidence]:
    """R3: Extended delay beyond category median completion time."""
    delay_ratio = row.get("delay_ratio")
    if delay_ratio is None or delay_ratio < 1.5:
        return None

    thresholds = RULES_CFG["r3_delay"]["overrun_thresholds"]
    points = 0
    for threshold, pts in thresholds:
        if delay_ratio >= threshold:
            points = pts

    if points == 0:
        return None

    stall_months = row.get("progress_stall_months", 0) or 0
    if stall_months >= 2:
        points += RULES_CFG["r3_delay"]["stall_bonus"]

    days_since = row.get("days_since_sanction", 0) or 0
    peer_median_dur = row.get("peer_median_duration", 0) or 0
    days_overdue = max(0, days_since - peer_median_dur) if peer_median_dur else 0

    return Evidence(
        code="R3_DELAY",
        dimension="temporal",
        points=points,
        headline=f"{days_overdue} days past category median completion window",
        detail=f"{days_overdue} days past the category median completion window (overrun ratio {delay_ratio:.1f}x){'; progress stalled for ' + str(stall_months) + ' consecutive months' if stall_months >= 2 else ''}",
        features={"days_overdue": days_overdue, "overrun_ratio": round(delay_ratio, 2), "stall_months": stall_months},
        peer_context={"median_duration": peer_median_dur},
        confidence="high" if days_since > 0 else "medium",
    )


def check_r4_payment_pattern(row: dict) -> Optional[Evidence]:
    """R4: Unusual payment pattern (front-loaded, clustered, single large)."""
    cfg = RULES_CFG["r4_payment_pattern"]
    points = 0
    sub_flags = []

    pct_before_50 = row.get("pct_paid_before_50_progress", 0) or 0
    if pct_before_50 >= 0.7:
        points += cfg["front_loaded_pts"]
        sub_flags.append("front-loaded")

    payment_gap_std = row.get("payment_gap_std", 0) or 0
    n_payments = row.get("n_payments", 0) or 0
    if payment_gap_std < 10 and n_payments >= 3:
        points += cfg["clustered_pts"]
        sub_flags.append("clustered")

    max_share = row.get("max_payment_share", 0) or 0
    if max_share >= 0.7:
        points += cfg["single_large_pts"]
        sub_flags.append("single large payment")

    points = min(points, cfg["cap"])

    if points == 0:
        return None

    return Evidence(
        code="R4_PAYMENT_PATTERN",
        dimension="payment",
        points=points,
        headline=f"Unusual payment pattern: {', '.join(sub_flags)}",
        detail=f"Payment pattern flags: {', '.join(sub_flags)}. {n_payments} payments, max single payment = {max_share*100:.0f}% of total, {pct_before_50*100:.0f}% released before 50% progress",
        features={"n_payments": n_payments, "max_payment_share": round(max_share, 3), "pct_before_50": round(pct_before_50, 3), "payment_gap_std": round(payment_gap_std, 1)},
        peer_context={},
        confidence="high" if n_payments >= 3 else "medium",
    )


def check_r5_utilisation(row: dict) -> Optional[Evidence]:
    """R5: Utilisation irregularity (over-expenditure or completed with very low spend)."""
    cfg = RULES_CFG["r5_utilisation"]
    util = row.get("utilisation_ratio", 0)
    status = row.get("status", "")

    if util is None:
        return None

    if util > 1.0:
        return Evidence(
            code="R5_UTILISATION",
            dimension="financial",
            points=cfg["over_1_pts"],
            headline=f"Expenditure exceeds sanctioned amount ({util*100:.0f}%)",
            detail=f"Utilisation ratio is {util:.2f} - expenditure exceeds the sanctioned amount by {(util-1)*100:.0f}%",
            features={"utilisation_ratio": round(util, 3)},
            peer_context={},
            confidence="high",
        )

    if status and "complet" in status.lower() and util < 0.4:
        return Evidence(
            code="R5_UTILISATION",
            dimension="financial",
            points=cfg["completed_under_04_pts"],
            headline=f"Completed with only {util*100:.0f}% of funds utilised",
            detail=f"Project marked as completed but only {util*100:.0f}% of sanctioned funds were utilised",
            features={"utilisation_ratio": round(util, 3), "status": status},
            peer_context={},
            confidence="medium",
        )

    return None


def check_r6_compliance(row: dict) -> Optional[Evidence]:
    """R6: Compliance completeness (missing mandatory elements)."""
    cfg = RULES_CFG["r6_compliance"]
    missing = []

    if not row.get("has_completion_cert") and row.get("status", "").lower() in ("completed", "complete"):
        missing.append("completion certificate")
    if not row.get("has_agency"):
        missing.append("implementing agency")
    if not row.get("has_geo"):
        missing.append("geo-coordinates")
    if not row.get("dates_consistent"):
        missing.append("consistent dates")

    if not missing:
        return None

    points = min(len(missing) * cfg["pts_per_missing"], cfg["cap"])

    return Evidence(
        code="R6_COMPLIANCE",
        dimension="compliance",
        points=points,
        headline=f"{len(missing)} missing/inconsistent mandatory element{'s' if len(missing) > 1 else ''}",
        detail=f"Missing or inconsistent: {', '.join(missing)}",
        features={"missing_elements": missing, "count": len(missing)},
        peer_context={},
        confidence="medium",
    )


def check_all(row: dict) -> list[Evidence]:
    """Run all 6 rules on a single project row. Returns list of Evidence objects."""
    evidence = []
    checkers = [
        check_r1_cost_deviation,
        check_r2_progress_mismatch,
        check_r3_delay,
        check_r4_payment_pattern,
        check_r5_utilisation,
        check_r6_compliance,
    ]
    for checker in checkers:
        result = checker(row)
        if result:
            evidence.append(result)
    return evidence
