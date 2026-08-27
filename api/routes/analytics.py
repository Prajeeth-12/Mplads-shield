import json
import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import Optional

from api.deps import get_db
from api.models import Project, RiskScore, AnomalyEvidence, Feature

router = APIRouter()

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "contracts")


@router.get("/analytics")
def get_analytics(state: Optional[str] = Query(None), db: Session = Depends(get_db)):
    count = db.query(RiskScore.project_id).first()
    if not count:
        with open(os.path.join(CONTRACTS_DIR, "analytics.json")) as f:
            return json.load(f)

    base_query = db.query(Project, RiskScore).outerjoin(RiskScore, Project.project_id == RiskScore.project_id)
    if state:
        base_query = base_query.filter(Project.state == state)

    state_risk = []
    state_rows = (
        db.query(
            Project.state,
            func.count(Project.project_id).label("total"),
            func.sum(case((RiskScore.tier == "HIGH", 1), else_=0)).label("high_count"),
            func.sum(case((RiskScore.tier == "CRITICAL", 1), else_=0)).label("critical_count"),
        )
        .outerjoin(RiskScore, Project.project_id == RiskScore.project_id)
        .group_by(Project.state)
        .all()
    )
    for s, total, high, crit in state_rows:
        high = high or 0
        crit = crit or 0
        state_risk.append({
            "state": s,
            "total": total,
            "high_count": high,
            "critical_count": crit,
            "high_risk_share": round((high + crit) / total, 3) if total else 0,
        })
    state_risk.sort(key=lambda x: x["high_risk_share"], reverse=True)

    category_anomaly = []
    cat_rows = (
        db.query(
            Project.category,
            func.count(Project.project_id).label("total"),
            func.sum(case((RiskScore.tier.in_(["HIGH", "CRITICAL"]), 1), else_=0)).label("high_count"),
        )
        .outerjoin(RiskScore, Project.project_id == RiskScore.project_id)
        .group_by(Project.category)
        .all()
    )
    for cat, total, high in cat_rows:
        high = high or 0
        category_anomaly.append({
            "category": cat,
            "total": total,
            "high_risk_pct": round(high / total, 3) if total else 0,
        })

    scatter = []
    scatter_rows = (
        db.query(Project.project_id, Feature.utilisation_ratio, Feature.progress_pct, RiskScore.tier)
        .join(Feature, Project.project_id == Feature.project_id)
        .outerjoin(RiskScore, Project.project_id == RiskScore.project_id)
        .filter(RiskScore.tier.in_(["HIGH", "CRITICAL"]))
        .limit(200)
        .all()
    )
    for pid, util, prog, tier in scatter_rows:
        scatter.append({
            "project_id": pid,
            "utilisation_pct": round(util * 100, 1) if util else 0,
            "progress_pct": round(prog, 1) if prog else 0,
            "tier": tier,
        })

    indicator_freq = []
    ind_rows = (
        db.query(AnomalyEvidence.code, func.count(AnomalyEvidence.evidence_id))
        .group_by(AnomalyEvidence.code)
        .order_by(desc(func.count(AnomalyEvidence.evidence_id)))
        .all()
    )
    label_map = {
        "R1_COST_DEVIATION": "Cost Overrun",
        "R2_PROGRESS_MISMATCH": "Progress Mismatch",
        "R3_DELAY": "Extended Delay",
        "R4_PAYMENT_PATTERN": "Payment Pattern",
        "R5_UTILISATION": "Utilisation Issue",
        "R6_COMPLIANCE": "Compliance Gap",
        "IF_ANOMALY": "ML Anomaly",
        "DUP_OVERLAP": "Duplicate/Overlap",
    }
    for code, cnt in ind_rows:
        indicator_freq.append({
            "indicator": code,
            "label": label_map.get(code, code),
            "count": cnt,
        })

    return {
        "state_risk": state_risk,
        "category_anomaly_rate": category_anomaly,
        "scatter": scatter,
        "indicator_frequency": indicator_freq,
    }
