import numpy as np
import pandas as pd
import yaml
import os
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from pipeline.evidence import Evidence

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

IF_CFG = CONFIG["isolation_forest"]


def run_isolation_forest(features_df: pd.DataFrame) -> list[dict]:
    """Run Isolation Forest on feature matrix. Returns list of {project_id, evidence} dicts."""

    os.makedirs(MODEL_DIR, exist_ok=True)

    feature_cols = IF_CFG["features"]
    available_cols = [c for c in feature_cols if c in features_df.columns]

    if len(available_cols) < 3:
        return []

    X = features_df[available_cols].copy()
    X = X.fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=IF_CFG["n_estimators"],
        contamination=IF_CFG["contamination"],
        random_state=IF_CFG["random_state"],
    )
    model.fit(X_scaled)

    joblib.dump(model, os.path.join(MODEL_DIR, "isolation_forest.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "if_scaler.joblib"))

    scores = model.score_samples(X_scaled)
    percentiles = pd.Series(scores).rank(pct=True) * 100

    threshold_pct = IF_CFG["threshold_percentile"]
    max_points = IF_CFG["max_points"]

    results = []
    for i, (idx, row) in enumerate(features_df.iterrows()):
        pct = percentiles.iloc[i]

        if pct > (100 - threshold_pct):
            continue

        anomaly_strength = (100 - threshold_pct - pct) / (100 - threshold_pct)
        points = round(max_points * min(1.0, anomaly_strength), 1)

        if points < 3:
            continue

        top_features = _get_top_features(X_scaled[i], available_cols, row, features_df)

        project_id = row.get("project_id", idx)
        evidence = Evidence(
            code="IF_ANOMALY",
            dimension="financial",
            points=points,
            headline=f"Unusual combination of features (ML anomaly, top {100-pct:.0f}%)",
            detail=f"Isolation Forest ranks this in the top {100-pct:.0f}% for unusual feature combination. Most anomalous features: {', '.join(top_features[:3])}",
            features={"anomaly_percentile": round(100 - pct, 1), "top_features": top_features[:3]},
            peer_context={"model": "IsolationForest", "n_estimators": IF_CFG["n_estimators"]},
            confidence="medium",
        )

        results.append({"project_id": project_id, "evidence": evidence})

    return results


def _get_top_features(scaled_row: np.ndarray, col_names: list, raw_row, features_df: pd.DataFrame) -> list[str]:
    """Get the 3 features with largest absolute deviation from 0 (standardized)."""
    abs_vals = np.abs(scaled_row)
    top_indices = np.argsort(abs_vals)[::-1][:3]

    readable_names = {
        "cost_z_score": "cost deviation",
        "utilisation_ratio": "utilisation",
        "progress_expenditure_gap": "progress-expenditure gap",
        "delay_ratio": "delay",
        "n_payments": "payment count",
        "max_payment_share": "payment concentration",
        "payment_gap_std": "payment timing",
        "progress_slope": "progress trajectory",
        "pct_paid_before_50_progress": "early payment share",
    }

    return [readable_names.get(col_names[i], col_names[i]) for i in top_indices]
