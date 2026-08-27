from sqlalchemy import Column, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from api.database import Base


class Agency(Base):
    __tablename__ = "agencies"
    agency_id = Column(Text, primary_key=True)
    agency_name = Column(Text, nullable=False)
    agency_type = Column(Text)
    district = Column(Text)
    state = Column(Text)


class Project(Base):
    __tablename__ = "projects"
    project_id = Column(Text, primary_key=True)
    work_name = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    district = Column(Text, nullable=False)
    constituency = Column(Text)
    mp_name = Column(Text)
    agency_id = Column(Text, ForeignKey("agencies.agency_id"))
    sanctioned_amount = Column(Float, nullable=False)
    sanction_date = Column(Text)
    expected_completion = Column(Text)
    actual_completion = Column(Text)
    status = Column(Text)
    lat = Column(Float)
    lon = Column(Float)
    has_completion_cert = Column(Integer, default=0)
    data_source = Column(Text, default="synthetic")
    fiscal_year = Column(Text)


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    txn_id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    txn_date = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    txn_type = Column(Text, default="release")
    milestone_progress_at_payment = Column(Float)


class ProgressUpdate(Base):
    __tablename__ = "progress_updates"
    update_id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    update_date = Column(Text, nullable=False)
    progress_pct = Column(Float, nullable=False)
    reported_by = Column(Text)
    remarks = Column(Text)


class Feature(Base):
    __tablename__ = "features"
    project_id = Column(Text, ForeignKey("projects.project_id"), primary_key=True)
    cost_per_unit = Column(Float)
    sanctioned_amount = Column(Float)
    total_expenditure = Column(Float)
    utilisation_ratio = Column(Float)
    progress_pct = Column(Float)
    progress_expenditure_gap = Column(Float)
    days_since_sanction = Column(Integer)
    expected_duration_days = Column(Integer)
    actual_duration_days = Column(Integer)
    delay_ratio = Column(Float)
    peer_median_cost = Column(Float)
    peer_mad_cost = Column(Float)
    cost_z_score = Column(Float)
    peer_median_duration = Column(Float)
    n_payments = Column(Integer)
    max_payment_share = Column(Float)
    payment_gap_mean = Column(Float)
    payment_gap_std = Column(Float)
    pct_paid_before_50_progress = Column(Float)
    progress_slope = Column(Float)
    progress_stall_months = Column(Integer)
    has_completion_cert = Column(Integer)
    has_agency = Column(Integer)
    has_geo = Column(Integer)
    dates_consistent = Column(Integer)
    description_length = Column(Integer)
    peer_group_key = Column(Text)
    peer_group_n = Column(Integer)
    computed_at = Column(DateTime, server_default=func.now())


class RiskScore(Base):
    __tablename__ = "risk_scores"
    project_id = Column(Text, ForeignKey("projects.project_id"), primary_key=True)
    total_score = Column(Float, nullable=False)
    tier = Column(Text, nullable=False)
    rank = Column(Integer)
    financial = Column(Float, default=0)
    progress = Column(Float, default=0)
    payment = Column(Float, default=0)
    duplication = Column(Float, default=0)
    temporal = Column(Float, default=0)
    compliance = Column(Float, default=0)
    model_version = Column(Text, default="v1.0")
    computed_at = Column(DateTime, server_default=func.now())


class RiskHistory(Base):
    __tablename__ = "risk_history"
    project_id = Column(Text, ForeignKey("projects.project_id"), primary_key=True)
    snapshot_date = Column(Text, primary_key=True)
    total_score = Column(Float, nullable=False)


class AnomalyEvidence(Base):
    __tablename__ = "anomaly_evidence"
    evidence_id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    code = Column(Text, nullable=False)
    dimension = Column(Text, nullable=False)
    points = Column(Float, nullable=False)
    headline = Column(Text, nullable=False)
    detail = Column(Text)
    features_json = Column(Text)
    peer_context_json = Column(Text)
    confidence = Column(Text, default="medium")


class DuplicatePair(Base):
    __tablename__ = "duplicate_pairs"
    pair_id = Column(Text, primary_key=True)
    project_a = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    project_b = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    similarity = Column(Float, nullable=False)
    distance_km = Column(Float)
    day_gap = Column(Integer)
    cost_ratio = Column(Float)
    same_agency = Column(Integer, default=0)


class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    severity = Column(Text, nullable=False)
    headline = Column(Text, nullable=False)
    recommended_action = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(Text, default="new")


class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.project_id"), nullable=False)
    reviewer_role = Column(Text)
    verdict = Column(Text, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
