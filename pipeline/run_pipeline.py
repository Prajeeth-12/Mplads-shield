"""MPLAD-SHIELD ML Pipeline Orchestrator.

Runs the full detection pipeline: features -> baselines -> rules -> IF -> duplicates -> fusion -> write DB.
"""
import os
import sys
import json
import uuid
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.baselines import compute_peer_baselines
from pipeline.rules import check_all
from pipeline.anomaly import run_isolation_forest
from pipeline.duplicates import find_duplicates
from pipeline.fusion import fuse
from pipeline.explain import generate_explanation
from pipeline.evidence import tier_of

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "mplad.db")


def run():
    print("=== MPLAD-SHIELD Pipeline ===")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    print("[1/8] Loading features...")
    features_df = pd.read_sql("SELECT * FROM features", conn, index_col="project_id")
    projects_df = pd.read_sql("SELECT project_id, description, category, state, district, sanction_date, sanctioned_amount, agency_id, status FROM projects", conn)

    if len(features_df) == 0:
        print("ERROR: No features found. Run data/seed.py first.")
        conn.close()
        return

    print(f"   Loaded {len(features_df)} projects with features")

    features_df["category"] = projects_df.set_index("project_id")["category"]
    features_df["state"] = projects_df.set_index("project_id")["state"]
    features_df["status"] = projects_df.set_index("project_id")["status"]

    print("[2/8] Computing peer baselines...")
    features_df = compute_peer_baselines(features_df)

    print("[3/8] Running 6 rule indicators...")
    all_evidence = {}
    for project_id, row in features_df.iterrows():
        row_dict = row.to_dict()
        row_dict["project_id"] = project_id
        evidence = check_all(row_dict)
        if evidence:
            all_evidence[project_id] = evidence

    rule_hits = sum(len(v) for v in all_evidence.values())
    print(f"   {rule_hits} rule hits across {len(all_evidence)} projects")

    print("[4/8] Running Isolation Forest...")
    features_for_if = features_df.copy()
    features_for_if["project_id"] = features_for_if.index
    if_results = run_isolation_forest(features_for_if)
    for item in if_results:
        pid = item["project_id"]
        if pid not in all_evidence:
            all_evidence[pid] = []
        all_evidence[pid].append(item["evidence"])
    print(f"   {len(if_results)} IF anomalies detected")

    print("[5/8] Running duplicate detection...")
    dup_pairs, dup_evidence = find_duplicates(projects_df)
    for item in dup_evidence:
        pid = item["project_id"]
        if pid not in all_evidence:
            all_evidence[pid] = []
        all_evidence[pid].append(item["evidence"])
    print(f"   {len(dup_pairs)} duplicate pairs found")

    print("[6/8] Fusing scores...")
    risk_scores = {}
    explanations = {}
    for project_id in features_df.index:
        evidence_list = all_evidence.get(project_id, [])
        score = fuse(evidence_list)
        risk_scores[project_id] = score
        explanations[project_id] = generate_explanation(evidence_list, score.tier)

    scores_sorted = sorted(risk_scores.items(), key=lambda x: -x[1].total)
    for rank, (pid, score) in enumerate(scores_sorted, 1):
        score.rank = rank

    tier_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for score in risk_scores.values():
        tier_counts[score.tier] = tier_counts.get(score.tier, 0) + 1
    print(f"   Tier distribution: {tier_counts}")

    print("[7/8] Writing to database...")
    conn.execute("DELETE FROM risk_scores")
    conn.execute("DELETE FROM anomaly_evidence")
    conn.execute("DELETE FROM alerts")
    conn.execute("DELETE FROM duplicate_pairs")

    for pid, score in risk_scores.items():
        conn.execute(
            "INSERT INTO risk_scores (project_id, total_score, tier, rank, financial, progress, payment, duplication, temporal, compliance) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pid, score.total, score.tier, score.rank,
             score.sub_scores.get("financial", 0), score.sub_scores.get("progress", 0),
             score.sub_scores.get("payment", 0), score.sub_scores.get("duplication", 0),
             score.sub_scores.get("temporal", 0), score.sub_scores.get("compliance", 0))
        )

    for pid, evidence_list in all_evidence.items():
        for e in evidence_list:
            eid = f"EV-{uuid.uuid4().hex[:8].upper()}"
            conn.execute(
                "INSERT INTO anomaly_evidence (evidence_id, project_id, code, dimension, points, headline, detail, features_json, peer_context_json, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (eid, pid, e.code, e.dimension, e.points, e.headline, e.detail,
                 json.dumps(e.features), json.dumps(e.peer_context), e.confidence)
            )

    for pair in dup_pairs:
        pair_id = f"DUP-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            "INSERT INTO duplicate_pairs (pair_id, project_a, project_b, similarity, distance_km, day_gap, cost_ratio, same_agency) VALUES (?,?,?,?,?,?,?,?)",
            (pair_id, pair["project_a"], pair["project_b"], pair["similarity"],
             pair.get("distance_km"), pair.get("day_gap"), pair.get("cost_ratio"), pair.get("same_agency", 0))
        )

    for pid, score in risk_scores.items():
        if score.tier in ("HIGH", "CRITICAL"):
            alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
            top_ev = score.top_evidence[0] if score.top_evidence else None
            headline = top_ev.headline if top_ev else f"Risk score {score.total}"
            action = explanations.get(pid, {}).get("action", "Review recommended")
            conn.execute(
                "INSERT INTO alerts (alert_id, project_id, severity, headline, recommended_action) VALUES (?,?,?,?,?)",
                (alert_id, pid, score.tier, headline, action)
            )

    conn.commit()

    print("[8/8] Writing risk history snapshot...")
    from datetime import date
    today = date.today().isoformat()
    for pid, score in risk_scores.items():
        try:
            conn.execute(
                "INSERT OR REPLACE INTO risk_history (project_id, snapshot_date, total_score) VALUES (?,?,?)",
                (pid, today, score.total)
            )
        except Exception:
            pass
    conn.commit()
    conn.close()

    print(f"\n=== Pipeline complete ===")
    print(f"   Total projects scored: {len(risk_scores)}")
    print(f"   Alerts generated: {sum(1 for s in risk_scores.values() if s.tier in ('HIGH', 'CRITICAL'))}")
    print(f"   Duplicate pairs: {len(dup_pairs)}")


if __name__ == "__main__":
    run()
