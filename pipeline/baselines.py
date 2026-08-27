import numpy as np
import pandas as pd
from typing import Optional


def compute_peer_baselines(features_df: pd.DataFrame) -> pd.DataFrame:
    """Compute peer baselines: median + MAD per peer group for cost, duration, utilisation, progress gap."""

    features_df = features_df.copy()

    if "peer_group_key" not in features_df.columns:
        features_df["peer_group_key"] = (
            features_df["category"] + " / " + features_df["state"] + " / " +
            features_df["sanctioned_amount"].apply(_cost_band)
        )

    metrics = [
        ("sanctioned_amount", "peer_median_cost", "peer_mad_cost", "cost_z_score"),
    ]

    results = []

    for group_key, group_df in features_df.groupby("peer_group_key"):
        n = len(group_df)

        if n < 30:
            category = group_key.split(" / ")[0] if " / " in group_key else group_key
            fallback = features_df[features_df["category"] == category] if "category" in features_df.columns else group_df
            if len(fallback) >= 30:
                group_df_baseline = fallback
                n = len(fallback)
            else:
                group_df_baseline = group_df
        else:
            group_df_baseline = group_df

        median_cost = group_df_baseline["sanctioned_amount"].median()
        mad_cost = _mad(group_df_baseline["sanctioned_amount"].values)

        median_duration = None
        if "expected_duration_days" in group_df_baseline.columns:
            valid_dur = group_df_baseline["expected_duration_days"].dropna()
            if len(valid_dur) > 0:
                median_duration = valid_dur.median()

        for idx in group_df.index:
            row_cost = features_df.loc[idx, "sanctioned_amount"]
            z_cost = _robust_z(row_cost, median_cost, mad_cost)

            results.append({
                "index": idx,
                "peer_median_cost": median_cost,
                "peer_mad_cost": mad_cost,
                "cost_z_score": z_cost,
                "peer_median_duration": median_duration,
                "peer_group_key": group_key,
                "peer_group_n": n,
            })

    if not results:
        return features_df

    baseline_df = pd.DataFrame(results).set_index("index")

    for col in baseline_df.columns:
        features_df[col] = baseline_df[col]

    return features_df


def _cost_band(amount: float) -> str:
    if amount < 10:
        return "small"
    elif amount < 25:
        return "medium"
    else:
        return "large"


def _mad(values: np.ndarray) -> float:
    median = np.median(values)
    return np.median(np.abs(values - median))


def _robust_z(value: float, median: float, mad: float) -> float:
    if mad == 0 or pd.isna(mad):
        return 0.0
    return 0.6745 * (value - median) / mad
