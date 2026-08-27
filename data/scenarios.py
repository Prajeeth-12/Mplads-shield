"""
MPLAD-SHIELD Demo Scenarios
============================
7 handcrafted cases designed to trigger specific risk indicators.
Each scenario explicitly constructs field values for deterministic testing.

Usage:
    python data/scenarios.py

Output:
    data/demo_projects.csv
    data/demo_transactions.csv
    data/demo_progress.csv
    data/demo_agencies.csv
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Agencies for demo cases
# ---------------------------------------------------------------------------

DEMO_AGENCIES = [
    {
        "agency_id": "AGY-DEMO-0001",
        "agency_name": "Sharma Construction",
        "registration_state": "Bihar",
        "registration_year": 2015,
        "category": "B",
    },
    {
        "agency_id": "AGY-DEMO-0002",
        "agency_name": "Rewa Builders Pvt Ltd",
        "registration_state": "Madhya Pradesh",
        "registration_year": 2012,
        "category": "A",
    },
    {
        "agency_id": "AGY-DEMO-0003",
        "agency_name": "Kalahandi Infrastructure",
        "registration_state": "Odisha",
        "registration_year": 2018,
        "category": "B",
    },
    {
        "agency_id": "AGY-DEMO-0004",
        "agency_name": "Jaunpur Civil Works",
        "registration_state": "Uttar Pradesh",
        "registration_year": 2016,
        "category": "B",
    },
    {
        "agency_id": "AGY-DEMO-0005",
        "agency_name": "Patna Road Constructions",
        "registration_state": "Bihar",
        "registration_year": 2014,
        "category": "A",
    },
    {
        "agency_id": "AGY-DEMO-0006",
        "agency_name": "Rajasthan Solar Solutions",
        "registration_state": "Rajasthan",
        "registration_year": 2019,
        "category": "C",
    },
    {
        "agency_id": "AGY-DEMO-0007",
        "agency_name": "Patna Road Constructions",
        "registration_state": "Bihar",
        "registration_year": 2014,
        "category": "A",
    },
]


def _date(y, m, d):
    return datetime(y, m, d)


def _fmt(dt):
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Case 1: Normal project (LOW risk, score ~8)
# ---------------------------------------------------------------------------

def case_1():
    pid = "MPL-BR-2024-0102"
    sanction_date = _date(2024, 1, 15)
    sanctioned_amount = 11.5  # lakhs - normal for community halls

    project = {
        "project_id": pid,
        "work_name": "Construction of Anganwadi Building, Ward 3, Nalanda",
        "category": "Community Halls",
        "state": "Bihar",
        "district": "Nalanda",
        "fiscal_year": "2023-24",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 12,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=365)),
        "status": "Completed",
        "final_progress_pct": 100.0,
        "has_completion_cert": 1,
        "agency_id": "AGY-DEMO-0001",
        "agency_name": "Sharma Construction",
        "mp_name": "MP_BR_05",
        "latitude": 25.13,
        "longitude": 85.44,
    }

    # 5 well-spaced payments
    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2024-02-10", "amount": 2.30,
         "txn_type": "Release", "milestone_progress_at_payment": 20.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2024-04-15", "amount": 2.50,
         "txn_type": "Release", "milestone_progress_at_payment": 40.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-06-20", "amount": 2.80,
         "txn_type": "Release", "milestone_progress_at_payment": 60.0},
        {"txn_id": f"TXN-{pid}-04", "project_id": pid,
         "txn_date": "2024-09-10", "amount": 2.10,
         "txn_type": "Release", "milestone_progress_at_payment": 80.0},
        {"txn_id": f"TXN-{pid}-05", "project_id": pid,
         "txn_date": "2024-12-01", "amount": 1.80,
         "txn_type": "Release", "milestone_progress_at_payment": 100.0},
    ]

    # Normal logistic progress
    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2024-02-15", "progress_pct": 12.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2024-04-15", "progress_pct": 35.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2024-06-15", "progress_pct": 58.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-08-15", "progress_pct": 78.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-10-15", "progress_pct": 93.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2024-12-15", "progress_pct": 100.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Case 2: Cost overrun (MEDIUM risk, score ~44) - R1 indicator
# Sanctioned 38L for community hall in MP where peer median is ~11L
# ---------------------------------------------------------------------------

def case_2():
    pid = "MPL-MP-2024-0233"
    sanction_date = _date(2024, 3, 10)
    sanctioned_amount = 38.0  # 3.4x the peer median of ~11L

    project = {
        "project_id": pid,
        "work_name": "Construction of community hall, Rewa",
        "category": "Community Halls",
        "state": "Madhya Pradesh",
        "district": "Rewa",
        "fiscal_year": "2023-24",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 12,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=365)),
        "status": "In Progress",
        "final_progress_pct": 65.0,
        "has_completion_cert": 0,
        "agency_id": "AGY-DEMO-0002",
        "agency_name": "Rewa Builders Pvt Ltd",
        "mp_name": "MP_MP_08",
        "latitude": 24.53,
        "longitude": 81.30,
    }

    # Normal payment pattern, just larger amounts
    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2024-04-20", "amount": 7.60,
         "txn_type": "Release", "milestone_progress_at_payment": 15.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2024-06-15", "amount": 8.50,
         "txn_type": "Release", "milestone_progress_at_payment": 35.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-08-25", "amount": 7.90,
         "txn_type": "Release", "milestone_progress_at_payment": 50.0},
        {"txn_id": f"TXN-{pid}-04", "project_id": pid,
         "txn_date": "2024-11-10", "amount": 6.00,
         "txn_type": "Release", "milestone_progress_at_payment": 65.0},
    ]

    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2024-04-10", "progress_pct": 8.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2024-06-10", "progress_pct": 28.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2024-08-10", "progress_pct": 45.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-10-10", "progress_pct": 58.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-12-10", "progress_pct": 63.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2025-02-10", "progress_pct": 65.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Case 3: Delay (MEDIUM risk, score ~38) - R3 indicator
# Sanctioned 26 months ago, only 35% progress, stalled last 3 months
# ---------------------------------------------------------------------------

def case_3():
    pid = "MPL-OD-2023-0781"
    sanction_date = _date(2023, 6, 15)
    sanctioned_amount = 14.5  # normal for bridges

    project = {
        "project_id": pid,
        "work_name": "Construction of culvert, Kalahandi",
        "category": "Bridges and Culverts",
        "state": "Odisha",
        "district": "Kalahandi",
        "fiscal_year": "2022-23",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 14,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=14 * 30)),
        "status": "In Progress",
        "final_progress_pct": 35.0,
        "has_completion_cert": 0,
        "agency_id": "AGY-DEMO-0003",
        "agency_name": "Kalahandi Infrastructure",
        "mp_name": "MP_OD_03",
        "latitude": 19.91,
        "longitude": 83.17,
    }

    # Few payments, then stalled
    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2023-08-10", "amount": 3.00,
         "txn_type": "Release", "milestone_progress_at_payment": 15.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2023-11-20", "amount": 2.50,
         "txn_type": "Release", "milestone_progress_at_payment": 28.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-03-05", "amount": 1.80,
         "txn_type": "Release", "milestone_progress_at_payment": 35.0},
    ]

    # Progress stalls after month 3
    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2023-07-15", "progress_pct": 8.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2023-09-15", "progress_pct": 20.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2023-11-15", "progress_pct": 30.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-01-15", "progress_pct": 33.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-03-15", "progress_pct": 34.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2024-05-15", "progress_pct": 35.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Case 4: Progress mismatch (HIGH risk, score ~57) - R2 indicator
# 82% funds released but only 25% physical progress
# ---------------------------------------------------------------------------

def case_4():
    pid = "MPL-UP-2024-0455"
    sanction_date = _date(2024, 2, 1)
    sanctioned_amount = 17.0  # normal for schools

    project = {
        "project_id": pid,
        "work_name": "Construction of school boundary wall, Jaunpur",
        "category": "Schools",
        "state": "Uttar Pradesh",
        "district": "Jaunpur",
        "fiscal_year": "2023-24",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 10,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=300)),
        "status": "In Progress",
        "final_progress_pct": 25.0,
        "has_completion_cert": 0,
        "agency_id": "AGY-DEMO-0004",
        "agency_name": "Jaunpur Civil Works",
        "mp_name": "MP_UP_11",
        "latitude": 25.75,
        "longitude": 82.68,
    }

    # 82% of 17L = 13.94L released, but progress only 25%
    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2024-02-20", "amount": 4.50,
         "txn_type": "Release", "milestone_progress_at_payment": 10.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2024-04-10", "amount": 4.20,
         "txn_type": "Release", "milestone_progress_at_payment": 18.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-06-05", "amount": 3.50,
         "txn_type": "Release", "milestone_progress_at_payment": 22.0},
        {"txn_id": f"TXN-{pid}-04", "project_id": pid,
         "txn_date": "2024-08-15", "amount": 1.74,
         "txn_type": "Release", "milestone_progress_at_payment": 25.0},
    ]

    # Progress barely moves despite heavy funding
    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2024-03-01", "progress_pct": 5.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2024-05-01", "progress_pct": 12.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2024-07-01", "progress_pct": 18.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-09-01", "progress_pct": 22.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-11-01", "progress_pct": 24.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2025-01-01", "progress_pct": 25.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Case 5: Duplicate pair with Case 7 (HIGH risk, score ~61)
# Near-identical description, same district, same agency, 41 days apart
# ---------------------------------------------------------------------------

def case_5():
    pid = "MPL-BR-2024-0388"
    sanction_date = _date(2024, 4, 20)  # 41 days after Case 7's sanction
    sanctioned_amount = 13.0  # normal for roads

    project = {
        "project_id": pid,
        "work_name": "Construction of CC road, Ward 7 extension, Danapur",
        "category": "Roads",
        "state": "Bihar",
        "district": "Patna",
        "fiscal_year": "2024-25",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 8,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=240)),
        "status": "In Progress",
        "final_progress_pct": 55.0,
        "has_completion_cert": 0,
        "agency_id": "AGY-DEMO-0005",
        "agency_name": "Patna Road Constructions",
        "mp_name": "MP_BR_02",
        "latitude": 25.62,
        "longitude": 85.05,
    }

    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2024-05-15", "amount": 3.20,
         "txn_type": "Release", "milestone_progress_at_payment": 20.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2024-07-10", "amount": 3.50,
         "txn_type": "Release", "milestone_progress_at_payment": 40.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-09-20", "amount": 2.80,
         "txn_type": "Release", "milestone_progress_at_payment": 55.0},
    ]

    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2024-05-20", "progress_pct": 10.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2024-06-20", "progress_pct": 25.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2024-07-20", "progress_pct": 38.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-08-20", "progress_pct": 45.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-09-20", "progress_pct": 52.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2024-10-20", "progress_pct": 55.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Case 6: Payment clustering (HIGH risk, score ~64) - R4 + IF indicators
# 3 payments in 11 days = 84% of total, before 50% progress
# ---------------------------------------------------------------------------

def case_6():
    pid = "MPL-RJ-2024-0620"
    sanction_date = _date(2024, 5, 1)
    sanctioned_amount = 9.5  # normal for solar

    project = {
        "project_id": pid,
        "work_name": "Installation of solar street lights, Bhilwara",
        "category": "Solar and Electrical",
        "state": "Rajasthan",
        "district": "Bhilwara",
        "fiscal_year": "2024-25",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 6,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=180)),
        "status": "In Progress",
        "final_progress_pct": 40.0,
        "has_completion_cert": 0,
        "agency_id": "AGY-DEMO-0006",
        "agency_name": "Rajasthan Solar Solutions",
        "mp_name": "MP_RJ_04",
        "latitude": 25.35,
        "longitude": 74.63,
    }

    # 3 payments in 11 days = 7.98L (84% of 9.5L), before 50% progress
    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2024-06-05", "amount": 2.80,
         "txn_type": "Release", "milestone_progress_at_payment": 15.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2024-06-10", "amount": 2.68,
         "txn_type": "Release", "milestone_progress_at_payment": 22.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-06-16", "amount": 2.50,
         "txn_type": "Release", "milestone_progress_at_payment": 30.0},
        {"txn_id": f"TXN-{pid}-04", "project_id": pid,
         "txn_date": "2024-09-20", "amount": 1.00,
         "txn_type": "Release", "milestone_progress_at_payment": 40.0},
    ]

    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2024-06-01", "progress_pct": 5.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2024-07-01", "progress_pct": 18.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2024-08-01", "progress_pct": 28.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-09-01", "progress_pct": 34.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-10-01", "progress_pct": 38.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2024-11-01", "progress_pct": 40.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Case 7: Hero case - ALL signals (CRITICAL risk, score ~87)
# R1: cost 42L (peer median 12.4L for roads in Bihar)
# R2: 84% spent / 30% progress
# R3: 214 days late
# R4: 3 clustered payments
# Duplicate: near-duplicate of Case 5
# Temporal: fiscal year-end clustering
# ---------------------------------------------------------------------------

def case_7():
    pid = "MPL-BR-2024-0417"
    sanction_date = _date(2024, 3, 10)  # 41 days before Case 5
    sanctioned_amount = 42.0  # 3.4x peer median of 12.4L for roads in Bihar

    project = {
        "project_id": pid,
        "work_name": "Construction of CC road, Ward 7, Danapur",
        "category": "Roads",
        "state": "Bihar",
        "district": "Patna",
        "fiscal_year": "2023-24",
        "sanction_date": _fmt(sanction_date),
        "sanctioned_amount": sanctioned_amount,
        "expected_duration_months": 8,
        "expected_completion_date": _fmt(sanction_date + timedelta(days=240)),
        "status": "In Progress",
        "final_progress_pct": 30.0,
        "has_completion_cert": 0,
        "agency_id": "AGY-DEMO-0005",
        "agency_name": "Patna Road Constructions",
        "mp_name": "MP_BR_02",
        "latitude": 25.61,
        "longitude": 85.04,
    }

    # 84% of 42L = 35.28L released. 3 clustered payments near fiscal year end
    # Total released: 35.28L
    transactions = [
        {"txn_id": f"TXN-{pid}-01", "project_id": pid,
         "txn_date": "2024-03-18", "amount": 12.00,
         "txn_type": "Release", "milestone_progress_at_payment": 10.0},
        {"txn_id": f"TXN-{pid}-02", "project_id": pid,
         "txn_date": "2024-03-22", "amount": 11.50,
         "txn_type": "Release", "milestone_progress_at_payment": 15.0},
        {"txn_id": f"TXN-{pid}-03", "project_id": pid,
         "txn_date": "2024-03-28", "amount": 8.78,
         "txn_type": "Release", "milestone_progress_at_payment": 20.0},
        {"txn_id": f"TXN-{pid}-04", "project_id": pid,
         "txn_date": "2024-07-15", "amount": 3.00,
         "txn_type": "Release", "milestone_progress_at_payment": 30.0},
    ]

    # Progress barely moves: 214 days past expected completion
    # Expected completion: 2024-03-10 + 240 days = 2024-11-05
    # Current date context: well past that
    progress = [
        {"update_id": f"UPD-{pid}-01", "project_id": pid,
         "update_date": "2024-04-10", "progress_pct": 5.0},
        {"update_id": f"UPD-{pid}-02", "project_id": pid,
         "update_date": "2024-06-10", "progress_pct": 12.0},
        {"update_id": f"UPD-{pid}-03", "project_id": pid,
         "update_date": "2024-08-10", "progress_pct": 18.0},
        {"update_id": f"UPD-{pid}-04", "project_id": pid,
         "update_date": "2024-10-10", "progress_pct": 24.0},
        {"update_id": f"UPD-{pid}-05", "project_id": pid,
         "update_date": "2024-12-10", "progress_pct": 28.0},
        {"update_id": f"UPD-{pid}-06", "project_id": pid,
         "update_date": "2025-02-10", "progress_pct": 30.0},
    ]

    return project, transactions, progress


# ---------------------------------------------------------------------------
# Build function
# ---------------------------------------------------------------------------

def build():
    """
    Build all 7 demo scenarios and return 4 DataFrames:
    projects_df, transactions_df, progress_df, agencies_df
    """
    case_funcs = [case_1, case_2, case_3, case_4, case_5, case_6, case_7]

    all_projects = []
    all_transactions = []
    all_progress = []

    for case_fn in case_funcs:
        project, transactions, progress = case_fn()
        all_projects.append(project)
        all_transactions.extend(transactions)
        all_progress.extend(progress)

    projects_df = pd.DataFrame(all_projects)
    transactions_df = pd.DataFrame(all_transactions)
    progress_df = pd.DataFrame(all_progress)
    agencies_df = pd.DataFrame(DEMO_AGENCIES)

    return projects_df, transactions_df, progress_df, agencies_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Build scenarios and save to CSV."""
    print("Building MPLAD-SHIELD demo scenarios...")

    projects_df, transactions_df, progress_df, agencies_df = build()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    projects_df.to_csv(OUTPUT_DIR / "demo_projects.csv", index=False)
    transactions_df.to_csv(OUTPUT_DIR / "demo_transactions.csv", index=False)
    progress_df.to_csv(OUTPUT_DIR / "demo_progress.csv", index=False)
    agencies_df.to_csv(OUTPUT_DIR / "demo_agencies.csv", index=False)

    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nFiles:")
    print(f"  demo_projects.csv     : {len(projects_df)} rows")
    print(f"  demo_transactions.csv : {len(transactions_df)} rows")
    print(f"  demo_progress.csv     : {len(progress_df)} rows")
    print(f"  demo_agencies.csv     : {len(agencies_df)} rows")

    print(f"\n{'='*60}")
    print("Demo Scenario Summary")
    print(f"{'='*60}")

    scenarios = [
        ("Case 1", "MPL-BR-2024-0102", "LOW (~8)", "Normal project - no indicators"),
        ("Case 2", "MPL-MP-2024-0233", "MEDIUM (~44)", "R1: Cost overrun (38L vs 11L median)"),
        ("Case 3", "MPL-OD-2023-0781", "MEDIUM (~38)", "R3: Delay (26mo elapsed, 35% progress)"),
        ("Case 4", "MPL-UP-2024-0455", "HIGH (~57)", "R2: Progress mismatch (82% funds, 25% progress)"),
        ("Case 5", "MPL-BR-2024-0388", "HIGH (~61)", "Duplicate of Case 7"),
        ("Case 6", "MPL-RJ-2024-0620", "HIGH (~64)", "R4+IF: 3 payments in 11 days (84% of total)"),
        ("Case 7", "MPL-BR-2024-0417", "CRITICAL (~87)", "R1+R2+R3+R4+Dup+Temporal (hero case)"),
    ]

    print(f"\n{'#':<6} {'Project ID':<20} {'Tier':<16} {'Indicators'}")
    print(f"{'-'*6} {'-'*20} {'-'*16} {'-'*45}")
    for case_name, pid, tier, indicators in scenarios:
        print(f"{case_name:<6} {pid:<20} {tier:<16} {indicators}")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
