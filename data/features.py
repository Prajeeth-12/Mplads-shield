"""Feature engineering: compute 28 features per project from raw data."""
import pandas as pd
import numpy as np
from datetime import datetime


def compute_features(projects_df: pd.DataFrame, transactions_df: pd.DataFrame, progress_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the 28-column feature table from raw project data."""

    projects_df = projects_df.copy()
    col_map = {
        "expected_completion_date": "expected_completion",
        "latitude": "lat",
        "longitude": "lon",
    }
    projects_df.rename(columns={k: v for k, v in col_map.items() if k in projects_df.columns}, inplace=True)

    if "description" not in projects_df.columns:
        projects_df["description"] = projects_df["work_name"]
    if "expected_completion" not in projects_df.columns:
        projects_df["expected_completion"] = None
    if "actual_completion" not in projects_df.columns:
        projects_df["actual_completion"] = None
    if "lat" not in projects_df.columns:
        projects_df["lat"] = None
    if "lon" not in projects_df.columns:
        projects_df["lon"] = None

    features = pd.DataFrame(index=projects_df["project_id"])
    features.index.name = "project_id"

    features["sanctioned_amount"] = projects_df.set_index("project_id")["sanctioned_amount"]

    txn_agg = transactions_df.groupby("project_id").agg(
        total_expenditure=("amount", "sum"),
        n_payments=("amount", "count"),
        max_payment=("amount", "max"),
    )
    features["total_expenditure"] = txn_agg["total_expenditure"]
    features["n_payments"] = txn_agg["n_payments"].astype("Int64")

    features["total_expenditure"] = features["total_expenditure"].fillna(0)
    features["n_payments"] = features["n_payments"].fillna(0)

    features["utilisation_ratio"] = (
        features["total_expenditure"] / features["sanctioned_amount"]
    ).clip(0, 2.0)

    features["cost_per_unit"] = features["sanctioned_amount"]

    prog_latest = progress_df.sort_values("update_date").groupby("project_id").last()
    features["progress_pct"] = prog_latest["progress_pct"]
    features["progress_pct"] = features["progress_pct"].fillna(0)

    features["progress_expenditure_gap"] = (
        features["utilisation_ratio"] * 100 - features["progress_pct"]
    )

    proj_indexed = projects_df.set_index("project_id")

    sanction_dates = pd.to_datetime(proj_indexed["sanction_date"], errors="coerce")
    reference_date = datetime(2024, 8, 15)
    features["days_since_sanction"] = (reference_date - sanction_dates).dt.days.astype("Int64")

    expected_comp = pd.to_datetime(proj_indexed["expected_completion"], errors="coerce")
    features["expected_duration_days"] = (expected_comp - sanction_dates).dt.days.astype("Int64")

    actual_comp = pd.to_datetime(proj_indexed["actual_completion"], errors="coerce")
    features["actual_duration_days"] = (actual_comp - sanction_dates).dt.days.astype("Int64")

    features["delay_ratio"] = np.where(
        features["expected_duration_days"] > 0,
        features["days_since_sanction"] / features["expected_duration_days"],
        0,
    )
    features["delay_ratio"] = features["delay_ratio"].clip(0, 10)

    max_share = txn_agg["max_payment"] / txn_agg["total_expenditure"]
    features["max_payment_share"] = max_share.clip(0, 1)
    features["max_payment_share"] = features["max_payment_share"].fillna(0)

    txn_sorted = transactions_df.sort_values(["project_id", "txn_date"])
    payment_gaps = []
    for pid, grp in txn_sorted.groupby("project_id"):
        dates = pd.to_datetime(grp["txn_date"], errors="coerce").dropna()
        if len(dates) >= 2:
            gaps = dates.diff().dt.days.dropna()
            payment_gaps.append({"project_id": pid, "gap_mean": gaps.mean(), "gap_std": gaps.std()})
        else:
            payment_gaps.append({"project_id": pid, "gap_mean": 0, "gap_std": 0})

    gap_df = pd.DataFrame(payment_gaps).set_index("project_id")
    features["payment_gap_mean"] = gap_df["gap_mean"]
    features["payment_gap_std"] = gap_df["gap_std"].fillna(0)

    pct_before_50 = []
    for pid, grp in transactions_df.groupby("project_id"):
        milestone = grp["milestone_progress_at_payment"].fillna(0)
        total = grp["amount"].sum()
        if total > 0:
            before_50 = grp[milestone < 50]["amount"].sum()
            pct_before_50.append({"project_id": pid, "pct": before_50 / total})
        else:
            pct_before_50.append({"project_id": pid, "pct": 0})

    pct_df = pd.DataFrame(pct_before_50).set_index("project_id")
    features["pct_paid_before_50_progress"] = pct_df["pct"]

    slope_data = []
    for pid, grp in progress_df.sort_values("update_date").groupby("project_id"):
        values = grp["progress_pct"].values
        if len(values) >= 2:
            slope = (values[-1] - values[0]) / len(values)
            stall = sum(1 for i in range(1, len(values)) if abs(values[i] - values[i-1]) < 2)
            stall_months = max(0, stall - 1) if stall >= 2 else 0
        else:
            slope = 0
            stall_months = 0
        slope_data.append({"project_id": pid, "slope": slope, "stall_months": stall_months})

    slope_df = pd.DataFrame(slope_data).set_index("project_id")
    features["progress_slope"] = slope_df["slope"]
    features["progress_stall_months"] = slope_df["stall_months"].astype("Int64")

    features["has_completion_cert"] = proj_indexed["has_completion_cert"].astype("Int64")
    features["has_agency"] = (proj_indexed["agency_id"].notna() & (proj_indexed["agency_id"] != "")).astype(int)
    features["has_geo"] = (proj_indexed["lat"].notna() & (proj_indexed["lat"] != 0)).astype(int)

    dates_ok = (sanction_dates.notna()) & (
        expected_comp.isna() | (expected_comp >= sanction_dates)
    )
    features["dates_consistent"] = dates_ok.astype(int)

    desc_col = proj_indexed["description"].fillna("")
    features["description_length"] = desc_col.str.len().astype("Int64")

    features["peer_median_cost"] = np.nan
    features["peer_mad_cost"] = np.nan
    features["cost_z_score"] = np.nan
    features["peer_median_duration"] = np.nan
    features["peer_group_key"] = ""
    features["peer_group_n"] = 0

    features = features.fillna(0)

    return features
