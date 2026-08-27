import yaml
import os
from pipeline.evidence import Evidence, RiskScore, tier_of

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

CAPS = CONFIG["scoring"]["caps"]


def fuse(evidence_list: list[Evidence]) -> RiskScore:
    """Fuse evidence into a capped additive risk score."""
    sub_scores = {dim: 0.0 for dim in CAPS}

    for e in evidence_list:
        dim = e.dimension
        if dim in sub_scores:
            sub_scores[dim] = min(CAPS[dim], sub_scores[dim] + e.points)

    total = round(sum(sub_scores.values()))
    tier = tier_of(total)
    top_evidence = sorted(evidence_list, key=lambda e: -e.points)[:5]

    return RiskScore(
        total=total,
        tier=tier,
        rank=None,
        sub_scores=sub_scores,
        top_evidence=top_evidence,
    )
