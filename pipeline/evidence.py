from dataclasses import dataclass, field, asdict
from typing import Optional


TIER_BANDS = [
    (80, "CRITICAL"),
    (55, "HIGH"),
    (30, "MEDIUM"),
    (0, "LOW"),
]


def tier_of(score: float) -> str:
    for threshold, name in TIER_BANDS:
        if score >= threshold:
            return name
    return "LOW"


@dataclass
class Evidence:
    code: str
    dimension: str
    points: float
    headline: str
    detail: str
    features: dict = field(default_factory=dict)
    peer_context: dict = field(default_factory=dict)
    confidence: str = "medium"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RiskScore:
    total: float
    tier: str
    rank: Optional[int]
    sub_scores: dict
    top_evidence: list

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "tier": self.tier,
            "rank": self.rank,
            "sub_scores": self.sub_scores,
            "top_evidence": [e.to_dict() for e in self.top_evidence],
        }
