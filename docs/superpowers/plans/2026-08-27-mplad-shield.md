# MPLAD-SHIELD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working AI-powered risk intelligence platform for MPLADS (SIH26102) that detects contextual anomalies, produces explainable 0-100 risk scores, and prioritizes cases for human investigation — with a demo-ready vertical slice.

**Architecture:** Python FastAPI backend serving precomputed scores from SQLite, fed by a batch ML pipeline (6 rule-based detectors + Isolation Forest + TF-IDF duplicate engine), consumed by a Vite+React+TypeScript+Tailwind frontend with 5 pages. Scores are assembled FROM explanations, never the reverse.

**Tech Stack:** Python 3.10+ (FastAPI, SQLAlchemy, pandas, numpy, scikit-learn, scipy), Node 18+ (Vite, React 18, TypeScript, Tailwind CSS, Recharts, React Router)

## Global Constraints

- SQLite only — no Postgres, Redis, Docker, or cloud services
- No auth/JWT — demo runs on localhost at 1920x1080
- Language discipline: "risk indicator" / "recommended for review" — never "fraud detected" or "guilty"
- All randomness seeded (`random_state=42`, `numpy.random.default_rng(42)`)
- Scores are precomputed batch — API is read-only (except review POST)
- Evidence dataclass is the frozen contract — score is assembled from evidence, not reverse-engineered

---

## Context

This is for Smart India Hackathon problem SIH26102 from MoSPI/DIID. The team (6 members, 24 hours) needs a working end-to-end demo showing: synthetic MPLADS data -> feature engineering -> anomaly detection -> explainable risk scoring -> dashboard with 7 demo cases. The key novelty is MPLADS-specific multi-dimensional risk fusion with contextual peer baselines and explainable investigation packets.

Three reference documents define the spec:
- `MPLAD-SHIELD_24h_War_Room_1.html` — 24-hour execution plan, architecture, API contracts, demo cases
- `SIH26102_MPLADS_Risk_Intelligence_End_to_End_Project_Brief.docx` — problem definition, research gap, novelty
- `SIH26102_MPLADS_Risk_Intelligence_MASTER_RESEARCH_IMPLEMENTATION_DOSSIER.docx` — exhaustive ML/module specs

---

## File Structure

```
mplad-shield/
├── run_all.sh / run_all.bat      # One-command: seed -> pipeline -> api -> frontend
├── requirements.txt              # Python deps
├── contracts/                    # 8 frozen API response example JSONs
├── data/
│   ├── generate_corpus.py        # 5,000 synthetic projects
│   ├── scenarios.py              # 7 deterministic demo cases
│   ├── clean.py                  # Normalisation
│   ├── features.py               # 28-column feature engineering
│   └── seed.py                   # CSV -> SQLite loader
├── pipeline/
│   ├── evidence.py               # THE frozen Evidence dataclass
│   ├── baselines.py              # Peer baseline engine (robust z-scores)
│   ├── rules.py                  # 6 rule indicators (R1-R6)
│   ├── anomaly.py                # Isolation Forest wrapper
│   ├── duplicates.py             # TF-IDF + cosine + gating
│   ├── fusion.py                 # Capped additive -> 0-100 + tiers
│   ├── explain.py                # Evidence -> human sentences
│   ├── run_pipeline.py           # Orchestrator: detect -> score -> write DB
│   └── config.yaml               # All thresholds, caps, weights
├── api/
│   ├── main.py                   # FastAPI app, CORS, routers
│   ├── database.py               # SQLAlchemy engine + session
│   ├── models.py                 # ORM models (9 tables)
│   ├── schemas.py                # Pydantic response models
│   └── routes/                   # One file per endpoint group
├── db/
│   ├── schema.sql                # 9 CREATE TABLE + indices
│   └── mplad.db                  # Committed scored DB (from Task 8 onward)
├── frontend/
│   ├── src/
│   │   ├── api.ts                # Mock/live switch client
│   │   ├── types.ts              # TS interfaces matching Pydantic schemas
│   │   ├── constants.ts          # Tier colors, labels
│   │   ├── components/           # RiskBadge, ScoreBar, EvidenceList, etc.
│   │   ├── pages/                # Overview, Monitor, ProjectDetail, Alerts, Analytics
│   │   └── mocks/                # Contract-derived mock JSON
│   └── ...config files
├── tests/
│   ├── test_rules.py             # Unit: exact points per rule
│   ├── test_fusion.py            # Caps, tiers
│   ├── test_api.py               # Smoke: 200 + keys
│   └── test_e2e.py               # 7 scenarios: correct tier + indicators
└── docs/
```

---

### Task 1: Project Foundation + Frozen Contracts

**Files:**
- Create: `requirements.txt`, `db/schema.sql`, `pipeline/__init__.py`, `pipeline/evidence.py`, `pipeline/config.yaml`
- Create: `contracts/overview.json`, `contracts/projects_list.json`, `contracts/project_detail.json`, `contracts/alerts.json`, `contracts/analytics.json`, `contracts/similar.json`, `contracts/review_response.json`

**Interfaces:**
- Produces: `Evidence` dataclass (consumed by ALL pipeline modules, API schemas, and frontend types), `config.yaml` (consumed by rules, fusion, anomaly), `schema.sql` (consumed by seed.py and SQLAlchemy models), 7 contract JSONs (consumed by API fixture responses and frontend mocks)

- [ ] **Step 1: Create `requirements.txt`**

```text
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pandas==2.2.3
numpy==1.26.4
scikit-learn==1.5.2
scipy==1.14.1
joblib==1.4.2
pydantic==2.9.0
pyyaml==6.0.2
pytest>=8.0.0
httpx>=0.27.0
requests>=2.32.0
```

- [ ] **Step 2: Create `db/schema.sql`**

9 tables: projects, agencies, financial_transactions, progress_updates, features, risk_scores, risk_history, anomaly_evidence, duplicate_pairs, alerts, reviews. Indices on risk_scores(total_score DESC), projects(state, district, category), anomaly_evidence(project_id).

```sql
CREATE TABLE projects(
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

CREATE TABLE agencies(
  agency_id TEXT PRIMARY KEY,
  agency_name TEXT NOT NULL,
  agency_type TEXT,
  district TEXT,
  state TEXT
);

CREATE TABLE financial_transactions(
  txn_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  txn_date DATE NOT NULL,
  amount REAL NOT NULL,
  txn_type TEXT DEFAULT 'release',
  milestone_progress_at_payment REAL
);

CREATE TABLE progress_updates(
  update_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  update_date DATE NOT NULL,
  progress_pct REAL NOT NULL,
  reported_by TEXT,
  remarks TEXT
);

CREATE TABLE features(
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

CREATE TABLE risk_scores(
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

CREATE TABLE risk_history(
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  snapshot_date DATE NOT NULL,
  total_score REAL NOT NULL,
  PRIMARY KEY(project_id, snapshot_date)
);

CREATE TABLE anomaly_evidence(
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

CREATE TABLE duplicate_pairs(
  pair_id TEXT PRIMARY KEY,
  project_a TEXT NOT NULL REFERENCES projects(project_id),
  project_b TEXT NOT NULL REFERENCES projects(project_id),
  similarity REAL NOT NULL,
  distance_km REAL,
  day_gap INTEGER,
  cost_ratio REAL,
  same_agency INTEGER DEFAULT 0
);

CREATE TABLE alerts(
  alert_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  severity TEXT NOT NULL,
  headline TEXT NOT NULL,
  recommended_action TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'new'
);

CREATE TABLE reviews(
  review_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(project_id),
  reviewer_role TEXT,
  verdict TEXT NOT NULL,
  note TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_scores_total ON risk_scores(total_score DESC);
CREATE INDEX idx_projects_state ON projects(state, district, category);
CREATE INDEX idx_evidence_project ON anomaly_evidence(project_id);
CREATE INDEX idx_alerts_severity ON alerts(severity, created_at DESC);
CREATE INDEX idx_transactions_project ON financial_transactions(project_id);
CREATE INDEX idx_progress_project ON progress_updates(project_id);
```

- [ ] **Step 3: Create `pipeline/evidence.py`**

The frozen Evidence dataclass + RiskScore dataclass + tier_of() helper.

```python
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class Evidence:
    code: str
    dimension: str
    points: float
    headline: str
    detail: str
    features: dict = field(default_factory=dict)
    peer_context: dict = field(default_factory=dict)
    confidence: str = "medium"

    def to_dict(self):
        return asdict(self)


@dataclass
class RiskScore:
    total: float
    tier: str
    rank: Optional[int]
    sub_scores: dict
    top_evidence: list

    def to_dict(self):
        return {
            "total": self.total,
            "tier": self.tier,
            "rank": self.rank,
            "sub_scores": self.sub_scores,
            "top_evidence": [e.to_dict() for e in self.top_evidence],
        }


TIER_BANDS = [
    (80, "CRITICAL"),
    (55, "HIGH"),
    (30, "MEDIUM"),
    (0, "LOW"),
]


def tier_of(score: float) -> str:
    for threshold, name in TIER_BANDS:
        if score >= threshold:
            return name
    return "LOW"
```

- [ ] **Step 4: Create `pipeline/config.yaml`**

```yaml
scoring:
  caps:
    financial: 25
    progress: 20
    payment: 18
    duplication: 15
    temporal: 12
    compliance: 10
  tiers:
    low: [0, 29]
    medium: [30, 54]
    high: [55, 79]
    critical: [80, 100]

rules:
  r1_cost_deviation:
    z_thresholds: [[2.0, 8], [2.5, 12], [3.0, 18], [4.0, 25]]
  r2_progress_mismatch:
    gap_thresholds: [[25, 8], [40, 14], [55, 20]]
  r3_delay:
    overrun_thresholds: [[1.5, 5], [2.0, 8], [3.0, 12]]
    stall_bonus: 2
  r4_payment_pattern:
    front_loaded_pts: 6
    clustered_pts: 6
    single_large_pts: 6
    cap: 18
  r5_utilisation:
    over_1_pts: 10
    completed_under_04_pts: 8
  r6_compliance:
    pts_per_missing: 2
    cap: 10

isolation_forest:
  n_estimators: 200
  contamination: 0.05
  random_state: 42
  max_points: 25
  threshold_percentile: 90
  features:
    - cost_z_score
    - utilisation_ratio
    - progress_expenditure_gap
    - delay_ratio
    - n_payments
    - max_payment_share
    - payment_gap_std
    - progress_slope
    - pct_paid_before_50_progress

duplicates:
  cosine_threshold: 0.72
  same_district: true
  same_category: true
  max_day_gap: 180
  cost_ratio_range: [0.6, 1.67]
  max_points: 15
  agency_differ_scale: 0.6

corpus:
  n_projects: 5000
  states: [Bihar, Uttar Pradesh, Madhya Pradesh, Odisha, Rajasthan, Maharashtra, Tamil Nadu, Karnataka, West Bengal, Jharkhand, Chhattisgarh, Gujarat]
  categories: [Roads, Community Halls, Schools, Hospitals, Water Supply, Drainage, Bridges and Culverts, Solar and Electrical]
  random_seed: 42
```

- [ ] **Step 5: Create 7 contract JSON files in `contracts/`**

Hand-write the exact response shapes for all 8 endpoints matching the schema from Part 10 of the War Room doc. Example for `contracts/project_detail.json`:

```json
{
  "project": {
    "project_id": "MPL-BR-2024-0417",
    "work_name": "Construction of CC road, Ward 7, Danapur",
    "description": "Construction of cement concrete road in Ward 7, Danapur municipality",
    "category": "Roads",
    "state": "Bihar",
    "district": "Patna",
    "constituency": "Pataliputra",
    "mp_name": "Demo MP",
    "agency_id": "AGN-BR-042",
    "sanctioned_amount": 42.0,
    "sanction_date": "2024-01-15",
    "expected_completion": "2024-09-15",
    "status": "In Progress",
    "data_source": "synthetic"
  },
  "financials": [
    {"txn_date": "2024-02-01", "amount": 12.0, "milestone_progress_at_payment": 0.10},
    {"txn_date": "2024-02-08", "amount": 12.5, "milestone_progress_at_payment": 0.15},
    {"txn_date": "2024-02-12", "amount": 10.8, "milestone_progress_at_payment": 0.20}
  ],
  "progress": [
    {"update_date": "2024-03-01", "progress_pct": 10},
    {"update_date": "2024-04-01", "progress_pct": 15},
    {"update_date": "2024-05-01", "progress_pct": 20},
    {"update_date": "2024-06-01", "progress_pct": 25},
    {"update_date": "2024-07-01", "progress_pct": 28},
    {"update_date": "2024-08-01", "progress_pct": 30}
  ],
  "score": {
    "total": 87,
    "tier": "CRITICAL",
    "rank": 12,
    "financial": 25,
    "progress": 20,
    "payment": 18,
    "duplication": 14,
    "temporal": 10,
    "compliance": 0
  },
  "evidence": [
    {
      "code": "R1_COST_DEVIATION",
      "dimension": "financial",
      "points": 25,
      "headline": "Cost 3.4x higher than comparable works",
      "detail": "Cost per km is 42.0 L against a peer median of 12.4 L for 1,240 comparable road works in Bihar (robust z = 3.4)",
      "features": {"cost_per_km": 42.0, "peer_median": 12.4, "z_score": 3.4},
      "peer_context": {"group": "Roads / Bihar / medium", "n": 1240, "median": 12.4},
      "confidence": "high"
    },
    {
      "code": "R2_PROGRESS_MISMATCH",
      "dimension": "progress",
      "points": 20,
      "headline": "84% funds released against 30% physical progress",
      "detail": "84% of funds released against 30% reported physical progress - a 54 percentage point gap where the peer median gap is 6 pp",
      "features": {"utilisation": 0.84, "progress": 0.30, "gap_pp": 54},
      "peer_context": {"group": "Roads / Bihar / medium", "n": 1240, "median_gap": 6},
      "confidence": "high"
    }
  ],
  "duplicates": [
    {
      "project_id": "MPL-BR-2024-0388",
      "work_name": "Construction of CC road, Ward 7 extension, Danapur",
      "similarity": 0.89,
      "day_gap": 41,
      "cost_ratio": 1.08,
      "same_agency": true
    }
  ],
  "history": [
    {"snapshot_date": "2024-03-01", "total_score": 32},
    {"snapshot_date": "2024-04-01", "total_score": 45},
    {"snapshot_date": "2024-05-01", "total_score": 52},
    {"snapshot_date": "2024-06-01", "total_score": 68},
    {"snapshot_date": "2024-07-01", "total_score": 78},
    {"snapshot_date": "2024-08-01", "total_score": 87}
  ],
  "explanation": {
    "summary": "Multiple independent risk indicators converge on this project. Cost is significantly above peers, funds have been released far ahead of physical progress, payments were clustered in an unusually short window, and a near-identical work exists in the same ward.",
    "reasons": [
      "Cost per km is 42.0 L against a peer median of 12.4 L for 1,240 comparable road works in Bihar (robust z = 3.4)",
      "84% of funds released against 30% reported physical progress (gap of 54 percentage points; peer median gap 6 pp)",
      "3 releases within 11 days totalling 84% of sanction, before the 50% progress milestone",
      "0.89 description similarity to MPL-BR-2024-0388, same district, same agency, sanctioned 41 days apart",
      "214 days past the category median completion window; risk score rose from 52 to 87 over the last two months"
    ],
    "action": "Priority field verification by District Authority",
    "confidence": "high"
  }
}
```

- [ ] **Step 6: Install Python deps and verify**

```bash
pip install -r requirements.txt
python -c "from pipeline.evidence import Evidence, RiskScore, tier_of; print('OK')"
```

---

### Task 2: FastAPI Backend Skeleton

**Files:**
- Create: `api/__init__.py`, `api/main.py`, `api/database.py`, `api/models.py`, `api/schemas.py`, `api/deps.py`
- Create: `api/routes/__init__.py`, `api/routes/overview.py`, `api/routes/projects.py`, `api/routes/alerts.py`, `api/routes/analytics.py`, `api/routes/similar.py`, `api/routes/review.py`

**Interfaces:**
- Consumes: `db/schema.sql` (table definitions), `contracts/*.json` (fixture responses), `pipeline/evidence.py` (Evidence type)
- Produces: 8 HTTP endpoints returning fixture JSON at localhost:8000, OpenAPI docs at /docs

- [ ] **Step 1: Create `api/database.py`**

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "mplad.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2: Create `api/models.py`**

SQLAlchemy ORM classes for all 9+2 tables matching `schema.sql`.

- [ ] **Step 3: Create `api/schemas.py`**

Pydantic response models: OverviewResponse, ProjectListResponse, ProjectDetailResponse, AlertResponse, AnalyticsResponse, SimilarResponse, ReviewRequest, ReviewResponse.

- [ ] **Step 4: Create route files**

Each route file is a FastAPI APIRouter. Initially return hardcoded fixture data from `contracts/`. Later (Task 8) repoint to real DB queries.

- [ ] **Step 5: Create `api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import overview, projects, alerts, analytics, similar, review

app = FastAPI(title="MPLAD-SHIELD API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(similar.router, prefix="/api")
app.include_router(review.router, prefix="/api")
```

- [ ] **Step 6: Test API**

```bash
cd api && uvicorn main:app --reload --port 8000
curl http://localhost:8000/api/overview
# Should return fixture JSON
# /docs should render OpenAPI UI
```

---

### Task 3: Synthetic Data Generation

**Files:**
- Create: `data/__init__.py`, `data/generate_corpus.py`, `data/scenarios.py`

**Interfaces:**
- Consumes: `db/schema.sql` (column names), `pipeline/config.yaml` (category distributions)
- Produces: `data/raw_projects.csv` (5,000 rows), `data/demo_projects.csv` (7 rows), payment/progress rows for each

- [ ] **Step 1: Create `data/generate_corpus.py`**

Generate 5,000 projects across 12 states, 40 districts, 8 categories:

- Amounts: log-normal per category (roads median ~12L, halls ~11L, schools ~18L, hospitals ~25L, water ~8L, drainage ~6L, bridges ~15L, solar ~10L)
- Duration: category-specific (roads ~8mo, buildings ~12mo, bridges ~14mo)
- Progress: 6 monthly snapshots following logistic curve + noise
- Payments: 3-8 installments, roughly milestone-aligned
- Agencies: 200 synthetic agencies with realistic names
- All seeded with `numpy.random.default_rng(42)`
- **ID collision prevention:** Use prefix `MPL-SYN-XXXX-NNNN` for synthetic IDs to avoid colliding with the deterministic demo case IDs (`MPL-BR-2024-0102`, `MPL-BR-2024-0388`, `MPL-BR-2024-0417`, etc.). The demo case IDs are reserved in `scenarios.py`.

- [ ] **Step 2: Create `data/scenarios.py`**

7 handcrafted demo cases with deliberately constructed field values:

| # | Project | Expected Score | Tier | Indicators |
|---|---------|---------------|------|------------|
| 1 | Anganwadi, Nalanda | 8 | LOW | None |
| 2 | Community hall, Rewa | 44 | MEDIUM | R1 |
| 3 | Culvert, Kalahandi | 38 | MEDIUM | R3 |
| 4 | School wall, Jaunpur | 57 | HIGH | R2 |
| 5 | CC road pair, Danapur | 61 | HIGH | Duplicate |
| 6 | Solar lights, Bhilwara | 64 | HIGH | R4 + IF |
| 7 | CC road (hero), Danapur | 87 | CRITICAL | R1+R2+R3+R4+Dup+Temporal |

Each case explicitly sets amounts, dates, progress, payments to trigger intended indicators.

- [ ] **Step 3: Run generators**

```bash
python data/generate_corpus.py
python data/scenarios.py
# Verify: raw_projects.csv has 5000 rows, demo_projects.csv has 7 rows
```

---

### Task 4: Data Cleaning + Feature Engineering + Seeding

**Files:**
- Create: `data/clean.py`, `data/features.py`, `data/seed.py`

**Interfaces:**
- Consumes: `data/raw_projects.csv`, `data/demo_projects.csv`, `db/schema.sql`
- Produces: SQLite DB with projects, agencies, financial_transactions, progress_updates, features tables populated (5,007 rows)

- [ ] **Step 1: Create `data/clean.py`**

Normalize dates to ISO, amounts to lakhs, categories to controlled vocabulary, validate expenditure <= sanctioned, flag missing fields. Never drop rows — flag them.

- [ ] **Step 2: Create `data/features.py`**

Compute 28 features per project:
- Financial: cost_per_unit, sanctioned_amount, total_expenditure, utilisation_ratio
- Progress: progress_pct, progress_expenditure_gap, progress_slope, progress_stall_months
- Temporal: days_since_sanction, expected_duration_days, actual_duration_days, delay_ratio
- Peer: peer_median_cost, peer_mad_cost, cost_z_score, peer_median_duration, peer_group_key, peer_group_n
- Payment: n_payments, max_payment_share, payment_gap_mean, payment_gap_std, pct_paid_before_50_progress
- Compliance: has_completion_cert, has_agency, has_geo, dates_consistent
- Text: description_length

- [ ] **Step 3: Create `data/seed.py`**

Load CSVs -> SQLite: create DB from schema.sql, insert projects + transactions + progress + agencies, run features.py, insert feature rows.

- [ ] **Step 4: Run full seed**

```bash
python data/seed.py
sqlite3 db/mplad.db "SELECT COUNT(*) FROM projects"       # -> 5007
sqlite3 db/mplad.db "SELECT COUNT(*) FROM features"       # -> 5007
sqlite3 db/mplad.db "SELECT COUNT(*) FROM financial_transactions"  # -> ~25000
```

---

### Task 5: Detection Pipeline (Rules + Baselines)

**Files:**
- Create: `pipeline/baselines.py`, `pipeline/rules.py`

**Interfaces:**
- Consumes: `features` table (28 columns), `pipeline/config.yaml` (thresholds), `pipeline/evidence.py` (Evidence class)
- Produces: `list[Evidence]` per project — each rule returns its evidence if triggered

- [ ] **Step 1: Create `pipeline/baselines.py`**

Peer baseline engine:
- Group by (category, state, cost_band), fallback to (category, national) if n<30
- Compute median + MAD (0.6745 * (x - median) / MAD) for cost, duration, utilisation, progress gap
- Return a DataFrame with peer_median, peer_mad, robust_z, peer_n per project

- [ ] **Step 2: Create `pipeline/rules.py` — all 6 rules**

Each rule: `def check_rX(row: dict, baselines: dict) -> Optional[Evidence]`

- R1 Cost deviation: z >= 2.0 -> 8pts, >=2.5 -> 12, >=3.0 -> 18, >=4.0 -> 25
- R2 Progress-expenditure mismatch: gap >= 25pp -> 8, >=40 -> 14, >=55 -> 20
- R3 Extended delay: overrun ratio >1.5 -> 5, >2.0 -> 8, >3.0 -> 12, +2 if stalled
- R4 Payment pattern: front-loaded(6) + clustered(6) + single-large(6), cap 18
- R5 Utilisation irregularity: >1.0 -> 10pts, completed with <0.4 -> 8pts
- R6 Compliance: 2pts per missing element (cert, agency, geo, dates), cap 10

Plus: `def check_all(row, baselines) -> list[Evidence]` running all 6.

- [ ] **Step 3: Test rules on demo cases**

```python
python -c "
from pipeline.rules import check_all
# Load Case 7 features, run check_all, verify R1=25, R2=20, R4=18
"
```

---

### Task 6: Isolation Forest + Duplicate Engine

**Files:**
- Create: `pipeline/anomaly.py`, `pipeline/duplicates.py`

**Interfaces:**
- Consumes: `features` table, `projects.description` column, `pipeline/config.yaml`
- Produces: Additional `Evidence` objects for IF anomalies, `duplicate_pairs` rows + Evidence

- [ ] **Step 1: Create `pipeline/anomaly.py`**

```python
# IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
# Fit on 9 scaled features from config
# score_samples -> percentile -> 0-25 points (only above 90th percentile)
# Evidence reports 3 features with largest |z| vs peer median
# Save model with joblib for reproducibility
```

- [ ] **Step 2: Create `pipeline/duplicates.py`**

```python
# TF-IDF vectorizer: char_wb (3,5) + word (1,2) n-grams
# Pairwise cosine within blocks (same district + same category)
# Gate: cosine >= 0.72, same district, same category, |day_gap| <= 180, cost_ratio 0.6-1.67
# Points: 15 * min(1, (cosine - 0.72) / 0.20)
# Scale down 40% if agencies differ
# Return duplicate_pairs + Evidence per pair
```

- [ ] **Step 3: Verify on demo data**

Case 5 pair (MPL-BR-2024-0388 / MPL-BR-2024-0417) should be found with similarity >= 0.85.
IF should flag Cases 6 and 7 above 90th percentile.

---

### Task 7: Risk Fusion + Explanation Builder + Pipeline Orchestrator

**Files:**
- Create: `pipeline/fusion.py`, `pipeline/explain.py`, `pipeline/run_pipeline.py`

**Interfaces:**
- Consumes: `list[Evidence]` per project from all detectors, `pipeline/config.yaml` (caps, tiers)
- Produces: `risk_scores` table, `anomaly_evidence` table, `alerts` table, `risk_history` rows in SQLite

- [ ] **Step 1: Create `pipeline/fusion.py`**

```python
def fuse(evidence_list: list[Evidence], config: dict) -> RiskScore:
    caps = config["scoring"]["caps"]
    sub = {d: 0.0 for d in caps}
    for e in evidence_list:
        sub[e.dimension] = min(caps[e.dimension], sub[e.dimension] + e.points)
    total = round(sum(sub.values()))
    tier = tier_of(total)
    top_evidence = sorted(evidence_list, key=lambda e: -e.points)[:5]
    return RiskScore(total=total, tier=tier, rank=None, sub_scores=sub, top_evidence=top_evidence)
```

- [ ] **Step 2: Create `pipeline/explain.py`**

Template-based: one sentence template per indicator code with interpolated numbers from evidence.features and evidence.peer_context.

```python
TEMPLATES = {
    "R1_COST_DEVIATION": "Cost per unit is {cost} L against a peer median of {median} L for {n} comparable {category} works in {state} (robust z = {z})",
    "R2_PROGRESS_MISMATCH": "{util_pct}% of funds released against {progress_pct}% reported physical progress - a {gap} percentage point gap where the peer median gap is {peer_gap} pp",
    # ... one per indicator code
}

def explain(evidence_list: list[Evidence]) -> dict:
    reasons = [format_template(e) for e in sorted(evidence_list, key=lambda e: -e.points)[:5]]
    summary = generate_summary(evidence_list)
    action = determine_action(tier)
    return {"summary": summary, "reasons": reasons, "action": action, "confidence": min_confidence(evidence_list)}
```

- [ ] **Step 3: Create `pipeline/run_pipeline.py`**

Main orchestrator:
1. Load features from DB
2. Compute peer baselines
3. Run all 6 rules -> list[Evidence] per project
4. Run Isolation Forest -> additional Evidence
5. Run duplicate engine -> pairs + Evidence
6. Fuse all evidence -> RiskScore per project
7. Assign ranks (by total_score DESC)
8. Generate explanations
9. Write risk_scores, anomaly_evidence, duplicate_pairs, alerts to DB
10. Write risk_history snapshot

- [ ] **Step 4: Run full pipeline and verify demo cases**

```bash
python pipeline/run_pipeline.py
# Verify:
sqlite3 db/mplad.db "SELECT project_id, total_score, tier FROM risk_scores WHERE project_id LIKE 'MPL-%' ORDER BY total_score DESC LIMIT 10"
# Case 7 should be CRITICAL (82-92), Case 1 should be LOW (5-15)
```

---

### Task 8: API Repointed to Live Data

**Files:**
- Modify: `api/routes/overview.py`, `api/routes/projects.py`, `api/routes/alerts.py`, `api/routes/analytics.py`, `api/routes/similar.py`, `api/routes/review.py`

**Interfaces:**
- Consumes: Scored `mplad.db` (from Task 7), `api/models.py` ORM models
- Produces: All 8 endpoints returning real scored data with pagination + filters

- [ ] **Step 1: Repoint GET /api/overview**

Query real aggregates: COUNT projects, SUM sanctioned/spent, tier_counts (GROUP BY tier), top 5 critical alerts (ORDER BY created_at DESC WHERE severity='CRITICAL'), state risk distribution (GROUP BY state).

- [ ] **Step 2: Repoint GET /api/projects**

Paginated query with filters: `?state=&district=&tier=&indicator=&min_score=&sort=score_desc&page=1&size=50`. JOIN risk_scores for score/tier. Return items with top_reason from first anomaly_evidence row.

- [ ] **Step 3: Repoint GET /api/projects/{id}**

Single response assembling: project row + financial_transactions + progress_updates + risk_scores + anomaly_evidence list + duplicate_pairs + risk_history + explanation (generated from evidence).

- [ ] **Step 4: Repoint remaining endpoints**

- GET /api/alerts: query alerts table, group by severity, join project name
- GET /api/analytics: aggregate queries for state_risk, category_anomaly_rate, scatter data, indicator_freq
- GET /api/projects/{id}/similar: query duplicate_pairs where project_a or project_b = id
- POST /api/projects/{id}/review: insert into reviews table, return review_id

- [ ] **Step 5: Verify all endpoints**

```bash
uvicorn api.main:app --port 8000
curl http://localhost:8000/api/projects/MPL-BR-2024-0417
# Should return full Case 7 detail with score 87, CRITICAL, 5 evidence items
```

---

### Task 9: React Frontend — Shell + Core Components

**Files:**
- Create: `frontend/` (full Vite scaffold)
- Create: `src/App.tsx`, `src/api.ts`, `src/types.ts`, `src/constants.ts`
- Create: `src/components/Layout.tsx`, `RiskBadge.tsx`, `ScoreBar.tsx`, `StatTile.tsx`, `EvidenceList.tsx`, `EvidenceItem.tsx`, `Disclaimer.tsx`, `FilterBar.tsx`, `ProjectTable.tsx`
- Create: `src/mocks/*.json`

**Interfaces:**
- Consumes: `contracts/*.json` (copied as mocks), API response types
- Produces: Running React app at :5173 with shell, nav, routing, core components, mock data layer

- [ ] **Step 1: Scaffold frontend**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install tailwindcss @tailwindcss/vite recharts react-router-dom
```

- [ ] **Step 2: Configure Tailwind v4 with tier color tokens**

In Tailwind v4, colors are defined via `@theme` in CSS (not tailwind.config.ts). Add to `src/index.css`:

```css
@import "tailwindcss";

@theme {
  --color-tier-low: #2C6A50;
  --color-tier-low-bg: #E2EFE8;
  --color-tier-med: #8A6212;
  --color-tier-med-bg: #F6EDD5;
  --color-tier-high: #AF4F1A;
  --color-tier-high-bg: #FAE6D8;
  --color-tier-crit: #9E1E2D;
  --color-tier-crit-bg: #F8DFE1;
  --color-accent: #24408E;
  --color-accent-soft: #E6EAF7;
}
```

Then in `vite.config.ts`, add the Tailwind plugin:

```typescript
import tailwindcss from "@tailwindcss/vite";
export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

- [ ] **Step 3: Create `api.ts` with mock/live switch**

```typescript
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function getOverview(): Promise<OverviewResponse> {
  if (USE_MOCKS) return (await import('./mocks/overview.json')).default;
  return fetch(`${BASE_URL}/api/overview`).then(r => r.json());
}
// ... one function per endpoint
```

- [ ] **Step 4: Create `types.ts` and `constants.ts`**

TypeScript interfaces matching all Pydantic response schemas. Tier color map, tier labels, risk dimension names.

- [ ] **Step 5: Create Layout + core components**

- Layout.tsx: sidebar nav (5 routes), header with "MPLAD-SHIELD" title, disclaimer footer
- RiskBadge.tsx: `<span>` with tier background color + text
- ScoreBar.tsx: horizontal bar showing value against cap with tier color
- StatTile.tsx: big number + label + optional trend indicator
- EvidenceItem.tsx: points badge + headline + detail + peer context
- EvidenceList.tsx: sorted list of EvidenceItems
- Disclaimer.tsx: "Risk indicators are investigation signals, not findings of wrongdoing."

- [ ] **Step 6: Copy mocks and verify app runs**

Copy contract JSONs into `src/mocks/`. Run `npm run dev`. App loads at :5173 with nav.

---

### Task 10: Frontend Pages (1-5)

**Files:**
- Create: `src/pages/Overview.tsx`, `Monitor.tsx`, `ProjectDetail.tsx`, `Alerts.tsx`, `Analytics.tsx`

**Interfaces:**
- Consumes: `api.ts` client functions, mock JSON data, component library from Task 9
- Produces: 5 fully rendered pages, ready for live API switch

- [ ] **Step 1: Page 1 — National Overview (`/`)**

- 4 StatTiles: total works (5,007), total sanctioned (sum lakhs), total spent, works under review
- Tier distribution: single stacked bar with counts (not pie chart)
- State risk ranking: horizontal bars sorted by % high-risk works
- Latest 5 critical alerts: each clickable to `/project/:id`
- Footer: data provenance note + disclaimer

- [ ] **Step 2: Page 2 — Risk Monitoring (`/monitor`)**

- ProjectTable: columns = ID, work name, district, category, sanctioned, spent, progress, score, tier chip, top reason
- FilterBar: state, district, category, tier, indicator type, min score
- Sort by score desc default, pagination at 50
- Row click -> `/project/:id`
- Tabular numerals for money columns

- [ ] **Step 3: Page 3 — Project Detail (`/project/:id`)**

THE demo centrepiece:
- Header: work name, ID, district, agency, MP, status, sanctioned vs spent
- Score panel: big "87", CRITICAL badge, "rank 12 of 5,007", 6 ScoreBars (financial/25, progress/20, payment/18, duplication/15, temporal/12, compliance/10)
- EvidenceList: ranked items with points badges, headlines, detail with numbers, peer context
- TwinTimeline: Recharts dual-line chart (cumulative expenditure + reported progress over time)
- TrajectoryChart: sparkline of total_score across 6 monthly snapshots
- DuplicatePanel: if duplicates exist, show side-by-side with similarity/gap/ratio
- ActionBar: "Mark Valid" / "False Positive" / "Send for Investigation" buttons + disclaimer

- [ ] **Step 4: Page 4 — Alerts (`/alerts`)**

- Grouped: CRITICAL section -> HIGH section -> MEDIUM section
- Each AlertCard: severity chip, work name, one-line headline, points, recommended action, "Open Project" link
- Status filter: new / under review / closed
- Every card ends with disclaimer

- [ ] **Step 5: Page 5 — Analytics (`/analytics`)**

- State risk bars: horizontal, sorted by high-risk share
- Category anomaly rate: bar chart showing % of works scoring HIGH+ per category
- Expenditure vs Progress scatter: Recharts scatter, x=utilisation%, y=progress%, points colored by tier, lower-right quadrant highlighted
- Indicator frequency: bar chart showing how often each of R1-R6 fires

- [ ] **Step 6: Switch to live API and verify**

```bash
# In frontend/.env:
VITE_USE_MOCKS=false
VITE_API_URL=http://localhost:8000

npm run dev
# Navigate: Page 1 -> click critical alert -> Page 3 for Case 7 -> read evidence
```

---

### Task 11: Integration + Testing + One-Command Boot

**Files:**
- Create: `run_all.sh`, `run_all.bat`
- Create: `tests/__init__.py`, `tests/test_e2e.py`, `tests/test_rules.py`, `tests/test_api.py`, `tests/test_fusion.py`
- Commit: `db/mplad.db`

**Interfaces:**
- Consumes: Everything from Tasks 1-10
- Produces: One-command demo boot, passing E2E tests, committed scored DB, offline fallback

- [ ] **Step 1: Create `run_all.sh` and `run_all.ps1`**

`run_all.sh` (bash/Linux/Mac/Git Bash):

```bash
#!/bin/bash
set -e
echo "=== MPLAD-SHIELD: Seeding database ==="
python data/seed.py
echo "=== MPLAD-SHIELD: Running ML pipeline ==="
python pipeline/run_pipeline.py
echo "=== MPLAD-SHIELD: Starting API server ==="
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "=== MPLAD-SHIELD: Starting frontend ==="
cd frontend && npm run dev &
FE_PID=$!
echo "=== MPLAD-SHIELD: Ready ==="
echo "  API: http://localhost:8000/docs"
echo "  UI:  http://localhost:5173"
wait $API_PID $FE_PID
```

`run_all.ps1` (Windows PowerShell — primary for this environment):

```powershell
Write-Host "=== MPLAD-SHIELD: Seeding database ==="
python data/seed.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "=== MPLAD-SHIELD: Running ML pipeline ==="
python pipeline/run_pipeline.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "=== MPLAD-SHIELD: Starting API server ==="
$api = Start-Process -NoNewWindow -PassThru -FilePath "uvicorn" -ArgumentList "api.main:app", "--host", "0.0.0.0", "--port", "8000"

Write-Host "=== MPLAD-SHIELD: Starting frontend ==="
$fe = Start-Process -NoNewWindow -PassThru -WorkingDirectory "frontend" -FilePath "npm" -ArgumentList "run", "dev"

Write-Host "=== MPLAD-SHIELD: Ready ==="
Write-Host "  API: http://localhost:8000/docs"
Write-Host "  UI:  http://localhost:5173"
Write-Host "  Press Ctrl+C to stop"

Wait-Process -Id $api.Id, $fe.Id
```

- [ ] **Step 2: Create `tests/test_e2e.py`**

Uses FastAPI's TestClient (from httpx) so tests run self-contained without a live server:

```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

DEMO_CASES = [
    ("MPL-BR-2024-0102", "LOW", (5, 15)),
    ("MPL-MP-2024-0233", "MEDIUM", (39, 49)),
    ("MPL-OD-2023-0781", "MEDIUM", (33, 43)),
    ("MPL-UP-2024-0455", "HIGH", (52, 62)),
    ("MPL-BR-2024-0388", "HIGH", (56, 66)),
    ("MPL-RJ-2024-0620", "HIGH", (59, 69)),
    ("MPL-BR-2024-0417", "CRITICAL", (82, 92)),
]

def test_all_scenarios():
    for project_id, expected_tier, (min_score, max_score) in DEMO_CASES:
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"]["tier"] == expected_tier
        assert min_score <= data["score"]["total"] <= max_score
        assert len(data["evidence"]) > 0 or expected_tier == "LOW"
        assert data["explanation"]["action"] is not None or expected_tier == "LOW"
```

- [ ] **Step 3: Create `tests/test_rules.py`**

6 handcrafted feature dicts — one per rule — asserting exact points output.

- [ ] **Step 4: Create `tests/test_fusion.py`**

Test cap enforcement (no dimension exceeds its cap), tier assignment, rank ordering.

- [ ] **Step 5: Create `tests/test_api.py`**

One request per endpoint: assert 200 status + required top-level keys.

- [ ] **Step 6: Full integration test**

```bash
# From clean state:
rm -f db/mplad.db
bash run_all.sh
# Wait 30s for startup
pytest tests/ -v
# All green -> commit db/mplad.db
```

- [ ] **Step 7: Create offline fallback**

Export API responses as static JSON to `frontend/public/static/`. Frontend detects if API is unreachable and falls back to static files.

---

## Verification Plan

1. **Unit tests:** `pytest tests/test_rules.py tests/test_fusion.py` — rules produce exact points, caps enforce, tiers correct
2. **API smoke:** `pytest tests/test_api.py` — all 8 endpoints return 200 with correct response shapes
3. **E2E scenarios:** `pytest tests/test_e2e.py` — 7 demo cases in correct tiers with correct indicators
4. **Visual verification:** Open browser at localhost:5173, navigate Page 1 -> click critical alert -> Page 3 for Case 7 -> read full evidence packet -> click "Investigate"
5. **Cold boot:** Delete mplad.db, run `run_all.sh`, verify demo works within 60 seconds
6. **Offline fallback:** Kill API process, refresh frontend, verify it still renders from static JSON
7. **Language audit:** Search entire frontend for "fraud", "guilty", "corrupt" — zero results

---

## Key Reusable Patterns

- **`pipeline/evidence.py`** — Evidence dataclass used by rules, fusion, API, and frontend (frozen, never changed)
- **`pipeline/config.yaml`** — single source of truth for all tunable parameters (thresholds, caps, weights, tiers)
- **`api.ts` mock/live switch** — frontend never blocked by backend status
- **Contract-first development** — `contracts/*.json` frozen at start, API and frontend both code against them
- **Score assembled from evidence** — the explanation IS the score, not a post-hoc interpretation
