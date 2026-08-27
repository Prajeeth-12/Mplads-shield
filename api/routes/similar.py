import json
import os
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models import DuplicatePair, Project

router = APIRouter()

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "contracts")


@router.get("/projects/{project_id}/similar")
def get_similar(project_id: str = Path(...), db: Session = Depends(get_db)):
    rows_a = (
        db.query(DuplicatePair, Project.work_name)
        .join(Project, DuplicatePair.project_b == Project.project_id)
        .filter(DuplicatePair.project_a == project_id)
        .all()
    )
    rows_b = (
        db.query(DuplicatePair, Project.work_name)
        .join(Project, DuplicatePair.project_a == Project.project_id)
        .filter(DuplicatePair.project_b == project_id)
        .all()
    )

    if not rows_a and not rows_b:
        with open(os.path.join(CONTRACTS_DIR, "similar.json")) as f:
            fixture = json.load(f)
        return fixture

    results = []
    for dup, wname in rows_a:
        results.append({
            "project_id": dup.project_b,
            "work_name": wname,
            "similarity": dup.similarity,
            "day_gap": dup.day_gap,
            "cost_ratio": dup.cost_ratio,
            "same_agency": bool(dup.same_agency),
        })
    for dup, wname in rows_b:
        results.append({
            "project_id": dup.project_a,
            "work_name": wname,
            "similarity": dup.similarity,
            "day_gap": dup.day_gap,
            "cost_ratio": dup.cost_ratio,
            "same_agency": bool(dup.same_agency),
        })

    return results
