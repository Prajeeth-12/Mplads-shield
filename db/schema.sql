-- MPLAD-SHIELD Database Schema
-- 9 core tables + 2 operational tables

CREATE TABLE IF NOT EXISTS agencies(
  agency_id TEXT PRIMARY KEY,
  agency_name TEXT NOT NULL,
  agency_type TEXT,
  district TEXT,
  state TEXT
);

CREATE TABLE IF NOT EXISTS projects(
  project_id TEXT PRIMARY KEY,
  work_name TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL,
  state TEXT NOT NULL,
  district TEXT NOT NULL,
  constituency TEXT,
  mp_name TEXT,
  agency_id TEXT REFERENCES agencies(agency_id),
  sanctioned_amount REAL NOT NULL,
  sanction_date DATE,
  expected_completion DATE,
  actual_completion DATE,
  status TEXT,
  lat REAL,
  lon REAL,
  has_completion_cert INTEGER DEFAULT 0,
  data_source TEXT DEFAULT 'synthetic',
  fiscal_year TEXT
);

CREATE TABLE IF NOT EXISTS financial_transactions(
  txn_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  txn_date DATE NOT NULL,
  amount REAL NOT NULL,
  txn_type TEXT DEFAULT 'release',
  milestone_progress_at_payment REAL
);

CREATE TABLE IF NOT EXISTS progress_updates(
  update_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  update_date DATE NOT NULL,
  progress_pct REAL NOT NULL,
  reported_by TEXT,
  remarks TEXT
);

CREATE TABLE IF NOT EXISTS features(
  project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
  cost_per_unit REAL,
  sanctioned_amount REAL,
  total_expenditure REAL,
  utilisation_ratio REAL,
  progress_pct REAL,
  progress_expenditure_gap REAL,
  days_since_sanction INTEGER,
  expected_duration_days INTEGER,
  actual_duration_days INTEGER,
  delay_ratio REAL,
  peer_median_cost REAL,
  peer_mad_cost REAL,
  cost_z_score REAL,
  peer_median_duration REAL,
  n_payments INTEGER,
  max_payment_share REAL,
  payment_gap_mean REAL,
  payment_gap_std REAL,
  pct_paid_before_50_progress REAL,
  progress_slope REAL,
  progress_stall_months INTEGER,
  has_completion_cert INTEGER,
  has_agency INTEGER,
  has_geo INTEGER,
  dates_consistent INTEGER,
  description_length INTEGER,
  peer_group_key TEXT,
  peer_group_n INTEGER,
  computed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_scores(
  project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
  total_score REAL NOT NULL,
  tier TEXT NOT NULL,
  rank INTEGER,
  financial REAL DEFAULT 0,
  progress REAL DEFAULT 0,
  payment REAL DEFAULT 0,
  duplication REAL DEFAULT 0,
  temporal REAL DEFAULT 0,
  compliance REAL DEFAULT 0,
  model_version TEXT DEFAULT 'v1.0',
  computed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_history(
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  snapshot_date DATE NOT NULL,
  total_score REAL NOT NULL,
  PRIMARY KEY(project_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS anomaly_evidence(
  evidence_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  code TEXT NOT NULL,
  dimension TEXT NOT NULL,
  points REAL NOT NULL,
  headline TEXT NOT NULL,
  detail TEXT,
  features_json TEXT,
  peer_context_json TEXT,
  confidence TEXT DEFAULT 'medium'
);

CREATE TABLE IF NOT EXISTS duplicate_pairs(
  pair_id TEXT PRIMARY KEY,
  project_a TEXT NOT NULL REFERENCES projects(project_id),
  project_b TEXT NOT NULL REFERENCES projects(project_id),
  similarity REAL NOT NULL,
  distance_km REAL,
  day_gap INTEGER,
  cost_ratio REAL,
  same_agency INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS alerts(
  alert_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  severity TEXT NOT NULL,
  headline TEXT NOT NULL,
  recommended_action TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS reviews(
  review_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  reviewer_role TEXT,
  verdict TEXT NOT NULL,
  note TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance indices
CREATE INDEX IF NOT EXISTS idx_risk_scores_total ON risk_scores(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state, district, category);
CREATE INDEX IF NOT EXISTS idx_evidence_project ON anomaly_evidence(project_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_project ON financial_transactions(project_id);
CREATE INDEX IF NOT EXISTS idx_progress_project ON progress_updates(project_id);
