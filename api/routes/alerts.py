import json
import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from api.deps import get_db
from api.models import Alert, Project, RiskScore

router = APIRouter()

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "contracts")


@router.get("/alerts")
def get_alerts(
    severity: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    count = db.query(Alert.alert_id).first()
    if not count:
        with open(os.path.join(CONTRACTS_DIR, "alerts.json")) as f:
            return json.load(f)

    query = (
        db.query(Alert, Project.work_name, RiskScore.total_score)
        .join(Project, Alert.project_id == Project.project_id)
        .outerjoin(RiskScore, Alert.project_id == RiskScore.project_id)
    )

    if severity:
        query = query.filter(Alert.severity == severity)
    if state:
        query = query.filter(Project.state == state)
    if status:
        query = query.filter(Alert.status == status)

    query = query.order_by(
        desc(Alert.severity == "CRITICAL"),
        desc(Alert.severity == "HIGH"),
        desc(Alert.severity == "MEDIUM"),
        desc(Alert.created_at),
    )

    rows = query.limit(100).all()

    return [
        {
            "alert_id": alert.alert_id,
            "project_id": alert.project_id,
            "work_name": work_name,
            "severity": alert.severity,
            "headline": alert.headline,
            "recommended_action": alert.recommended_action,
            "score": score,
            "created_at": str(alert.created_at) if alert.created_at else None,
            "status": alert.status,
        }
        for alert, work_name, score in rows
    ]
