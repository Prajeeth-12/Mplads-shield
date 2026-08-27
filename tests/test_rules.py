"""Unit tests for the 6 rule indicators."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.rules import (
    check_r1_cost_deviation,
    check_r2_progress_mismatch,
    check_r3_delay,
    check_r4_payment_pattern,
    check_r5_utilisation,
    check_r6_compliance,
)


def test_r1_fires_at_z_3():
    row = {"cost_z_score": 3.2, "sanctioned_amount": 42.0, "peer_median_cost": 12.0,
           "peer_mad_cost": 3.0, "peer_group_key": "Roads / Bihar / large", "peer_group_n": 1200}
    result = check_r1_cost_deviation(row)
    assert result is not None
    assert result.code == "R1_COST_DEVIATION"
    assert result.points == 18
    assert result.dimension == "financial"


def test_r1_no_fire_below_threshold():
    row = {"cost_z_score": 1.5, "sanctioned_amount": 15.0, "peer_median_cost": 12.0,
           "peer_mad_cost": 3.0, "peer_group_key": "Roads / Bihar / medium", "peer_group_n": 100}
    assert check_r1_cost_deviation(row) is None


def test_r2_fires_at_55pp_gap():
    row = {"utilisation_ratio": 0.86, "progress_pct": 30.0}
    result = check_r2_progress_mismatch(row)
    assert result is not None
    assert result.code == "R2_PROGRESS_MISMATCH"
    assert result.points == 20  # gap = 56pp >= 55 threshold


def test_r2_fires_at_25pp_gap():
    row = {"utilisation_ratio": 0.60, "progress_pct": 30.0}
    result = check_r2_progress_mismatch(row)
    assert result is not None
    assert result.points == 8


def test_r3_fires_with_stall():
    row = {"delay_ratio": 2.5, "days_since_sanction": 500, "peer_median_duration": 240,
           "progress_stall_months": 3}
    result = check_r3_delay(row)
    assert result is not None
    assert result.code == "R3_DELAY"
    assert result.points == 10  # 8 for ratio 2.0+ plus 2 stall bonus


def test_r4_all_sub_flags():
    row = {"pct_paid_before_50_progress": 0.85, "payment_gap_std": 5.0,
           "n_payments": 4, "max_payment_share": 0.75}
    result = check_r4_payment_pattern(row)
    assert result is not None
    assert result.points == 18  # 6+6+6, capped at 18


def test_r5_over_expenditure():
    row = {"utilisation_ratio": 1.15, "status": "In Progress"}
    result = check_r5_utilisation(row)
    assert result is not None
    assert result.points == 10


def test_r5_completed_low_util():
    row = {"utilisation_ratio": 0.35, "status": "Completed"}
    result = check_r5_utilisation(row)
    assert result is not None
    assert result.points == 8


def test_r6_missing_elements():
    row = {"has_completion_cert": 0, "has_agency": 0, "has_geo": 0, "dates_consistent": 0,
           "status": "Completed"}
    result = check_r6_compliance(row)
    assert result is not None
    assert result.points == 8  # 4 missing x 2pts each, but cap is 10


def test_r6_no_fire_when_complete():
    row = {"has_completion_cert": 1, "has_agency": 1, "has_geo": 1, "dates_consistent": 1,
           "status": "Completed"}
    assert check_r6_compliance(row) is None
