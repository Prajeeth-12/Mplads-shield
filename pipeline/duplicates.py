import numpy as np
import pandas as pd
import yaml
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pipeline.evidence import Evidence

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

DUP_CFG = CONFIG["duplicates"]


def find_duplicates(projects_df: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Find potential duplicate works using TF-IDF + structured gating.

    Returns:
        pairs: list of dicts for duplicate_pairs table
        evidence_items: list of {project_id, evidence} dicts
    """
    if "description" not in projects_df.columns or len(projects_df) < 10:
        return [], []

    df = projects_df[["project_id", "description", "district", "category",
                       "sanction_date", "sanctioned_amount", "agency_id"]].copy()
    df = df.dropna(subset=["description"])
    df["description"] = df["description"].fillna("").str.lower().str.strip()
    df = df[df["description"].str.len() > 10]

    if len(df) < 10:
        return [], []

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=10000,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(df["description"])

    pairs = []
    evidence_items = []

    for district in df["district"].unique():
        for category in df["category"].unique():
            block = df[(df["district"] == district) & (df["category"] == category)]
            if len(block) < 2:
                continue

            block_indices = block.index.tolist()
            block_positions = [df.index.get_loc(i) for i in block_indices]
            block_tfidf = tfidf_matrix[block_positions]

            sim_matrix = cosine_similarity(block_tfidf)

            for i in range(len(block)):
                for j in range(i + 1, len(block)):
                    cos_sim = sim_matrix[i, j]
                    if cos_sim < DUP_CFG["cosine_threshold"]:
                        continue

                    row_a = block.iloc[i]
                    row_b = block.iloc[j]

                    day_gap = _day_gap(row_a.get("sanction_date"), row_b.get("sanction_date"))
                    if day_gap is not None and day_gap > DUP_CFG["max_day_gap"]:
                        continue

                    amt_a = row_a.get("sanctioned_amount", 0) or 1
                    amt_b = row_b.get("sanctioned_amount", 0) or 1
                    cost_ratio = amt_a / amt_b if amt_b > 0 else 1
                    min_ratio, max_ratio = DUP_CFG["cost_ratio_range"]
                    if cost_ratio < min_ratio or cost_ratio > max_ratio:
                        continue

                    same_agency = int(row_a.get("agency_id") == row_b.get("agency_id"))

                    points = DUP_CFG["max_points"] * min(1.0, (cos_sim - DUP_CFG["cosine_threshold"]) / 0.20)
                    if not same_agency:
                        points *= DUP_CFG["agency_differ_scale"]
                    points = round(points, 1)

                    if points < 2:
                        continue

                    pair = {
                        "project_a": row_a["project_id"],
                        "project_b": row_b["project_id"],
                        "similarity": round(cos_sim, 3),
                        "distance_km": None,
                        "day_gap": day_gap,
                        "cost_ratio": round(cost_ratio, 3),
                        "same_agency": same_agency,
                    }
                    pairs.append(pair)

                    for pid in [row_a["project_id"], row_b["project_id"]]:
                        other_id = row_b["project_id"] if pid == row_a["project_id"] else row_a["project_id"]
                        ev = Evidence(
                            code="DUP_OVERLAP",
                            dimension="duplication",
                            points=points,
                            headline=f"{cos_sim:.2f} similarity to {other_id}",
                            detail=f"{cos_sim:.2f} description similarity to {other_id}, same district, {'same' if same_agency else 'different'} agency, sanctioned {day_gap or '?'} days apart, cost ratio {cost_ratio:.2f}",
                            features={"similarity": round(cos_sim, 3), "day_gap": day_gap, "cost_ratio": round(cost_ratio, 3)},
                            peer_context={"matched_project": other_id, "same_agency": bool(same_agency)},
                            confidence="high" if cos_sim >= 0.85 else "medium",
                        )
                        evidence_items.append({"project_id": pid, "evidence": ev})

    return pairs, evidence_items


def _day_gap(date_a, date_b) -> int | None:
    if not date_a or not date_b:
        return None
    try:
        from datetime import datetime
        da = datetime.fromisoformat(str(date_a)[:10])
        db = datetime.fromisoformat(str(date_b)[:10])
        return abs((da - db).days)
    except (ValueError, TypeError):
        return None
