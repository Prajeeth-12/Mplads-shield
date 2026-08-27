import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models import Review
from api.schemas import ReviewRequest, ReviewResponse

router = APIRouter()


@router.post("/projects/{project_id}/review")
def submit_review(
    project_id: str = Path(...),
    body: ReviewRequest = ...,
    db: Session = Depends(get_db),
) -> ReviewResponse:
    review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow().isoformat()

    review = Review(
        review_id=review_id,
        project_id=project_id,
        reviewer_role=body.reviewer_role,
        verdict=body.verdict,
        note=body.note,
    )
    db.add(review)
    db.commit()

    return ReviewResponse(
        ok=True,
        review_id=review_id,
        project_id=project_id,
        verdict=body.verdict,
        reviewer_role=body.reviewer_role,
        created_at=now,
    )
