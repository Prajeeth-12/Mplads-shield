import json
import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional

from api.deps import get_db
from api.models import Project, RiskScore, Alert, AnomalyEvidence

router = APIRouter()

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "contracts")


def _load_fixture():
    with open(os.path.join(CONTRACTS_DIR, "overview.json")) as f:
        return json.load(f)


@router.get("/overview")
def get_overview(state: Optional[str] = Query(None), db: Session = Depends(get_db)):
    project_count = db.query(func.count(Project.project_id)).scalar()

    if not project_count:
        return _load_fixture()

    total_sanctioned = db.query(func.sum(Project.sanctioned_amount)).scalar() or 0

    from api.models import Feature
    total_spent = db.query(func.sum(Feature.total_expenditure)).scalar() or 0

    tier_counts = {}
    tier_rows = db.query(RiskScore.tier, func.count(RiskScore.project_id)).group_by(RiskScore.tier).all()
    for tier, count in tier_rows:
        tier_counts[tier] = count

    critical_alerts = []
    alert_rows = (
        db.query(Alert, Project.work_name, RiskScore.total_score)
        .join(Project, Alert.project_id == Project.project_id)
        .outerjoin(RiskScore, Alert.project_id == RiskScore.project_id)
        .filter(Alert.severity == "CRITICAL")
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )
    for alert, work_name, score in alert_rows:
        critical_alerts.append({
            "alert_id": alert.alert_id,
            "project_id": alert.project_id,
            "work_name": work_name,
            "severity": alert.severity,
            "headline": alert.headline,
            "score": score,
        })

    state_risk = []
    state_query = (
        db.query(
            Project.state,
            func.count(Project.project_id).label("total"),
            func.sum(case((RiskScore.tier.in_(["HIGH", "CRITICAL"]), 1), else_=0)).label("high_count"),
        )
        .outerjoin(RiskScore, Project.project_id == RiskScore.project_id)
        .group_by(Project.state)
        .all()
    )
    for s, total, high_count in state_query:
        high_count = high_count or 0
        state_risk.append({
            "state": s,
            "total": total,
            "high_risk_share": round(high_count / total, 3) if total > 0 else 0,
        })
    state_risk.sort(key=lambda x: x["high_risk_share"], reverse=True)

    indicator_freq = []
    ind_rows = (
        db.query(AnomalyEvidence.code, func.count(AnomalyEvidence.evidence_id))
        .group_by(AnomalyEvidence.code)
        .all()
    )
    for code, count in ind_rows:
        indicator_freq.append({"indicator": code, "count": count})

    return {
        "total_projects": project_count,
        "total_sanctioned": round(total_sanctioned, 1),
        "total_spent": round(total_spent, 1),
        "tier_counts": tier_counts,
        "critical_alerts": critical_alerts,
        "state_risk": state_risk,
        "indicator_frequency": indicator_freq,
    }
