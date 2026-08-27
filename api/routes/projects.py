import json
import os
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from api.deps import get_db
from api.models import (
    Project, RiskScore, AnomalyEvidence, FinancialTransaction,
    ProgressUpdate, DuplicatePair, RiskHistory, Feature
)

router = APIRouter()

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "contracts")


@router.get("/projects")
def list_projects(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    indicator: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    sort: Optional[str] = Query("score_desc"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    project_count = db.query(Project.project_id).first()
    if not project_count:
        with open(os.path.join(CONTRACTS_DIR, "projects_list.json")) as f:
            return json.load(f)

    query = (
        db.query(Project, RiskScore, Feature)
        .outerjoin(RiskScore, Project.project_id == RiskScore.project_id)
        .outerjoin(Feature, Project.project_id == Feature.project_id)
    )

    if state:
        query = query.filter(Project.state == state)
    if district:
        query = query.filter(Project.district == district)
    if tier:
        query = query.filter(RiskScore.tier == tier)
    if min_score is not None:
        query = query.filter(RiskScore.total_score >= min_score)

    if indicator:
        subq = db.query(AnomalyEvidence.project_id).filter(AnomalyEvidence.code == indicator).subquery()
        query = query.filter(Project.project_id.in_(subq))

    total = query.count()

    if sort == "score_desc":
        query = query.order_by(desc(RiskScore.total_score))
    elif sort == "score_asc":
        query = query.order_by(RiskScore.total_score)
    else:
        query = query.order_by(desc(RiskScore.total_score))

    rows = query.offset((page - 1) * size).limit(size).all()

    items = []
    for project, risk, feat in rows:
        top_evidence = (
            db.query(AnomalyEvidence.headline)
            .filter(AnomalyEvidence.project_id == project.project_id)
            .order_by(desc(AnomalyEvidence.points))
            .first()
        )
        items.append({
            "project_id": project.project_id,
            "work_name": project.work_name,
            "district": project.district,
            "category": project.category,
            "sanctioned_amount": project.sanctioned_amount,
            "total_expenditure": feat.total_expenditure if feat else 0,
            "progress_pct": feat.progress_pct if feat else None,
            "score": risk.total_score if risk else 0,
            "tier": risk.tier if risk else "LOW",
            "top_reason": top_evidence[0] if top_evidence else None,
        })

    return {"total": total, "page": page, "size": size, "items": items}


@router.get("/projects/{project_id}")
def get_project_detail(project_id: str = Path(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_id == project_id).first()

    if not project:
        with open(os.path.join(CONTRACTS_DIR, "project_detail.json")) as f:
            fixture = json.load(f)
        if fixture["project"]["project_id"] == project_id:
            return fixture
        raise HTTPException(status_code=404, detail="Project not found")

    risk = db.query(RiskScore).filter(RiskScore.project_id == project_id).first()

    financials = (
        db.query(FinancialTransaction)
        .filter(FinancialTransaction.project_id == project_id)
        .order_by(FinancialTransaction.txn_date)
        .all()
    )

    progress = (
        db.query(ProgressUpdate)
        .filter(ProgressUpdate.project_id == project_id)
        .order_by(ProgressUpdate.update_date)
        .all()
    )

    evidence_rows = (
        db.query(AnomalyEvidence)
        .filter(AnomalyEvidence.project_id == project_id)
        .order_by(desc(AnomalyEvidence.points))
        .all()
    )

    dup_rows = (
        db.query(DuplicatePair, Project.work_name)
        .join(Project, DuplicatePair.project_b == Project.project_id)
        .filter(DuplicatePair.project_a == project_id)
        .all()
    )
    dup_rows_b = (
        db.query(DuplicatePair, Project.work_name)
        .join(Project, DuplicatePair.project_a == Project.project_id)
        .filter(DuplicatePair.project_b == project_id)
        .all()
    )

    history = (
        db.query(RiskHistory)
        .filter(RiskHistory.project_id == project_id)
        .order_by(RiskHistory.snapshot_date)
        .all()
    )

    project_dict = {
        "project_id": project.project_id,
        "work_name": project.work_name,
        "description": project.description,
        "category": project.category,
        "state": project.state,
        "district": project.district,
        "constituency": project.constituency,
        "mp_name": project.mp_name,
        "agency_id": project.agency_id,
        "sanctioned_amount": project.sanctioned_amount,
        "sanction_date": project.sanction_date,
        "expected_completion": project.expected_completion,
        "actual_completion": project.actual_completion,
        "status": project.status,
        "data_source": project.data_source,
    }

    score_dict = {
        "total": risk.total_score if risk else 0,
        "tier": risk.tier if risk else "LOW",
        "rank": risk.rank if risk else None,
        "financial": risk.financial if risk else 0,
        "progress": risk.progress if risk else 0,
        "payment": risk.payment if risk else 0,
        "duplication": risk.duplication if risk else 0,
        "temporal": risk.temporal if risk else 0,
        "compliance": risk.compliance if risk else 0,
    }

    evidence_list = []
    for e in evidence_rows:
        evidence_list.append({
            "code": e.code,
            "dimension": e.dimension,
            "points": e.points,
            "headline": e.headline,
            "detail": e.detail,
            "features": json.loads(e.features_json) if e.features_json else {},
            "peer_context": json.loads(e.peer_context_json) if e.peer_context_json else {},
            "confidence": e.confidence,
        })

    duplicates = []
    for dup, wname in dup_rows:
        duplicates.append({
            "project_id": dup.project_b,
            "work_name": wname,
            "similarity": dup.similarity,
            "day_gap": dup.day_gap,
            "cost_ratio": dup.cost_ratio,
            "same_agency": bool(dup.same_agency),
        })
    for dup, wname in dup_rows_b:
        duplicates.append({
            "project_id": dup.project_a,
            "work_name": wname,
            "similarity": dup.similarity,
            "day_gap": dup.day_gap,
            "cost_ratio": dup.cost_ratio,
            "same_agency": bool(dup.same_agency),
        })

    reasons = [e["detail"] or e["headline"] for e in evidence_list[:5]]
    top_tier = score_dict["tier"]
    if top_tier == "CRITICAL":
        action = "Priority field verification by District Authority"
    elif top_tier == "HIGH":
        action = "Recommended for desk review"
    elif top_tier == "MEDIUM":
        action = "Watch list; re-check next reporting cycle"
    else:
        action = "No action required"

    explanation = {
        "summary": f"{'Multiple independent risk indicators converge.' if len(evidence_list) >= 3 else evidence_list[0]['headline'] if evidence_list else 'No risk indicators.'}",
        "reasons": reasons,
        "action": action,
        "confidence": evidence_list[0]["confidence"] if evidence_list else "low",
    }

    return {
        "project": project_dict,
        "financials": [
            {"txn_date": t.txn_date, "amount": t.amount, "milestone_progress_at_payment": t.milestone_progress_at_payment}
            for t in financials
        ],
        "progress": [{"update_date": p.update_date, "progress_pct": p.progress_pct} for p in progress],
        "score": score_dict,
        "evidence": evidence_list,
        "duplicates": duplicates,
        "history": [{"snapshot_date": h.snapshot_date, "total_score": h.total_score} for h in history],
        "explanation": explanation,
    }
