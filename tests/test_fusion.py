"""Unit tests for risk fusion logic."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.evidence import Evidence, tier_of
from pipeline.fusion import fuse


def test_tier_bands():
    assert tier_of(87) == "CRITICAL"
    assert tier_of(80) == "CRITICAL"
    assert tier_of(79) == "HIGH"
    assert tier_of(55) == "HIGH"
    assert tier_of(54) == "MEDIUM"
    assert tier_of(30) == "MEDIUM"
    assert tier_of(29) == "LOW"
    assert tier_of(0) == "LOW"


def test_fusion_caps_dimensions():
    evidence = [
        Evidence(code="R1", dimension="financial", points=30, headline="", detail=""),
        Evidence(code="R5", dimension="financial", points=10, headline="", detail=""),
    ]
    score = fuse(evidence)
    assert score.sub_scores["financial"] == 25  # capped at 25


def test_fusion_total():
    evidence = [
        Evidence(code="R1", dimension="financial", points=25, headline="", detail=""),
        Evidence(code="R2", dimension="progress", points=20, headline="", detail=""),
        Evidence(code="R4", dimension="payment", points=18, headline="", detail=""),
    ]
    score = fuse(evidence)
    assert score.total == 63
    assert score.tier == "HIGH"


def test_fusion_critical():
    evidence = [
        Evidence(code="R1", dimension="financial", points=25, headline="", detail=""),
        Evidence(code="R2", dimension="progress", points=20, headline="", detail=""),
        Evidence(code="R4", dimension="payment", points=18, headline="", detail=""),
        Evidence(code="DUP", dimension="duplication", points=15, headline="", detail=""),
        Evidence(code="R3", dimension="temporal", points=12, headline="", detail=""),
    ]
    score = fuse(evidence)
    assert score.total == 90
    assert score.tier == "CRITICAL"


def test_fusion_empty():
    score = fuse([])
    assert score.total == 0
    assert score.tier == "LOW"
    assert score.top_evidence == []


def test_top_evidence_limited_to_5():
    evidence = [
        Evidence(code=f"R{i}", dimension="financial", points=5, headline=f"item {i}", detail="")
        for i in range(10)
    ]
    score = fuse(evidence)
    assert len(score.top_evidence) == 5
