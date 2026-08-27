from pydantic import BaseModel
from typing import Optional


class AlertBrief(BaseModel):
    alert_id: str
    project_id: str
    work_name: str
    severity: str
    headline: str
    score: Optional[float] = None
    recommended_action: Optional[str] = None
    created_at: Optional[str] = None
    status: Optional[str] = "new"


class StateRisk(BaseModel):
    state: str
    total: int
    high_risk_share: float
    high_count: Optional[int] = None
    critical_count: Optional[int] = None


class OverviewResponse(BaseModel):
    total_projects: int
    total_sanctioned: float
    total_spent: float
    tier_counts: dict
    critical_alerts: list[AlertBrief]
    state_risk: list[StateRisk]
    indicator_frequency: list[dict]


class ProjectListItem(BaseModel):
    project_id: str
    work_name: str
    district: str
    category: str
    sanctioned_amount: float
    total_expenditure: float
    progress_pct: Optional[float] = None
    score: float
    tier: str
    top_reason: Optional[str] = None


class ProjectListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ProjectListItem]


class EvidenceItem(BaseModel):
    code: str
    dimension: str
    points: float
    headline: str
    detail: Optional[str] = None
    features: Optional[dict] = None
    peer_context: Optional[dict] = None
    confidence: Optional[str] = "medium"


class ScoreDetail(BaseModel):
    total: float
    tier: str
    rank: Optional[int] = None
    financial: float = 0
    progress: float = 0
    payment: float = 0
    duplication: float = 0
    temporal: float = 0
    compliance: float = 0


class TransactionItem(BaseModel):
    txn_id: Optional[str] = None
    txn_date: str
    amount: float
    txn_type: Optional[str] = "release"
    milestone_progress_at_payment: Optional[float] = None


class ProgressItem(BaseModel):
    update_date: str
    progress_pct: float


class DuplicateItem(BaseModel):
    project_id: str
    work_name: Optional[str] = None
    similarity: float
    day_gap: Optional[int] = None
    cost_ratio: Optional[float] = None
    same_agency: Optional[bool] = None


class HistoryItem(BaseModel):
    snapshot_date: str
    total_score: float


class ExplanationDetail(BaseModel):
    summary: str
    reasons: list[str]
    action: str
    confidence: str = "medium"


class ProjectDetailResponse(BaseModel):
    project: dict
    financials: list[TransactionItem]
    progress: list[ProgressItem]
    score: ScoreDetail
    evidence: list[EvidenceItem]
    duplicates: list[DuplicateItem]
    history: list[HistoryItem]
    explanation: ExplanationDetail


class ReviewRequest(BaseModel):
    verdict: str
    note: Optional[str] = None
    reviewer_role: Optional[str] = None


class ReviewResponse(BaseModel):
    ok: bool
    review_id: str
    project_id: str
    verdict: str
    reviewer_role: Optional[str] = None
    created_at: Optional[str] = None
