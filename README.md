# MPLAD-SHIELD

**AI-Powered Risk Intelligence Platform for MPLADS Works**

> Smart Monitoring of Financial, Execution, Semantic and Compliance Risks in MPLAD Scheme Implementation

**Problem Statement:** SIH26102 | **Organization:** Ministry of Statistics & Programme Implementation (MoSPI) | **Division:** Data Informatics & Innovation Division (DIID)

---

## What It Does

MPLAD-SHIELD is an AI-assisted risk-intelligence layer over MPLADS (Member of Parliament Local Area Development Scheme) data. It analyzes 5,000+ development works and answers: **which projects should a district officer look at first, and why?**

- Detects contextual anomalies using peer baselines (not fixed thresholds)
- Produces explainable risk scores (0-100) across 6 dimensions
- Prioritizes cases for human investigation
- **Never declares fraud** — only "risk indicators" and "recommended for review"

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### One-Command Setup

**Windows (PowerShell):**
```powershell
pip install -r requirements.txt
cd frontend && npm install && cd ..
.\run_all.ps1
```

**Linux/Mac:**
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
bash run_all.sh
```

### Manual Start (if DB already seeded)

```bash
# Terminal 1: API
uvicorn api.main:app --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

- **Dashboard:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

---

## Architecture

```
DATA SOURCES (eSAKSHI structure + synthetic corpus)
       │
       ▼
INGESTION & GENERATION (5,000 projects + 7 demo cases)
       │
       ▼
FEATURE ENGINEERING (28 named features)
       │
       ▼
DETECTION (parallel)
  ┌────────┬──────────┬──────────────┬──────────┐
  │ 6 Rules│ Peer     │ Isolation    │ TF-IDF   │
  │ (R1-R6)│ Baseline │ Forest       │ Duplicate│
  └────┬───┴────┬─────┴──────┬───────┴────┬─────┘
       └────────┴────────────┴────────────┘
                      │
                      ▼
RISK FUSION (capped additive, 0-100)
                      │
                      ▼
EXPLANATION BUILDER (evidence → sentences)
                      │
                      ▼
SQLite DB (precomputed scores) → FastAPI (8 endpoints) → React Dashboard (5 pages)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React 18 + TypeScript + Tailwind CSS v4 + Recharts |
| API | FastAPI + Pydantic + Uvicorn |
| Database | SQLite + SQLAlchemy |
| ML Pipeline | pandas + numpy + scikit-learn + scipy |
| NLP | scikit-learn TF-IDF (duplicate detection) |

---

## Risk Scoring

6 dimensions with hard caps:

| Dimension | Cap | Question |
|-----------|-----|----------|
| Financial | 25 | Does this cost what comparable works cost? |
| Progress | 20 | Has money moved faster than the work? |
| Payment | 18 | Is money leaving in an unusual rhythm? |
| Duplication | 15 | Might this work already have been funded? |
| Temporal | 12 | Is it late, and getting worse? |
| Compliance | 10 | Is the record itself sound? |
| **Total** | **100** | **Investigation priority — not a verdict** |

### Tiers
- **LOW** (0-29): ~70% of projects — no action
- **MEDIUM** (30-54): ~20% — watch list
- **HIGH** (55-79): ~8% — recommended for desk review
- **CRITICAL** (80-100): ~2% — priority field verification

---

## 6 Detection Rules

| Rule | Detects | Method |
|------|---------|--------|
| R1 | Cost overrun vs peers | Robust z-score (median + MAD) |
| R2 | Progress-expenditure mismatch | Gap >= 25 percentage points |
| R3 | Extended delay | Duration overrun ratio vs peer median |
| R4 | Unusual payment pattern | Front-loaded + clustered + single-large |
| R5 | Utilisation irregularity | Over-expenditure or completed with low spend |
| R6 | Compliance completeness | Missing certificate, agency, geo-tag, dates |

---

## 7 Demo Cases

| # | Project | Score | Tier | Demonstrates |
|---|---------|-------|------|-------------|
| 1 | Anganwadi building, Nalanda | 8 | LOW | Normal baseline |
| 2 | Community hall, Rewa | 44 | MEDIUM | Cost overrun |
| 3 | Culvert, Kalahandi | 38 | MEDIUM | Extended delay |
| 4 | School wall, Jaunpur | 57 | HIGH | Progress mismatch |
| 5 | CC road pair, Danapur | 61 | HIGH | Duplicate detection |
| 6 | Solar lights, Bhilwara | 64 | HIGH | Payment pattern + ML |
| 7 | CC road (hero), Danapur | 87 | CRITICAL | All signals converge |

---

## Dashboard Pages

1. **National Overview** (`/`) — stat tiles, tier distribution, state risk ranking
2. **Risk Monitoring** (`/monitor`) — sortable project table with filters
3. **Project Detail** (`/project/:id`) — score panel, evidence list, timeline charts
4. **Alerts** (`/alerts`) — severity-grouped investigation queue
5. **Analytics** (`/analytics`) — state trends, category rates, indicator frequency

---

## Project Structure

```
mplad-shield/
├── api/              # FastAPI backend (8 endpoints)
├── pipeline/         # ML detection pipeline
│   ├── evidence.py   # Frozen Evidence dataclass
│   ├── baselines.py  # Peer baseline engine
│   ├── rules.py      # 6 rule indicators
│   ├── anomaly.py    # Isolation Forest
│   ├── duplicates.py # TF-IDF duplicate detection
│   ├── fusion.py     # Capped additive scoring
│   └── explain.py    # Evidence → sentences
├── data/             # Data generation & seeding
├── frontend/         # React dashboard
├── db/               # SQLite schema & database
├── contracts/        # Frozen API response contracts
├── tests/            # pytest test suite
└── run_all.ps1       # One-command startup
```

---

## Testing

```bash
pytest tests/ -v
# 24 tests: rules, fusion, API endpoints
```

---

## Key Design Principles

1. **Scores are precomputed** — API never calls a model at request time
2. **Rules first, ML second** — 6 deterministic rules carry 70% of value
3. **Explanation is first-class** — score is assembled FROM evidence
4. **Language discipline** — "recommended for review", never "fraud detected"
5. **Context over thresholds** — peer baselines compare to comparable works
6. **Human decides** — system ranks, officials investigate

---

## Novelty

> A project-centric, MPLADS-specific risk-intelligence framework that fuses financial, execution, temporal, semantic and compliance evidence into explainable risk profiles and prioritized early-warning cases for human investigation.

---

## Team

Built for Smart India Hackathon 2026 (SIH26102)

---

*Risk indicators are investigation signals, not findings of wrongdoing.*
