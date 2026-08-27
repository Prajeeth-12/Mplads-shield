# MPLAD-SHIELD

**Smart Monitoring of Financial, Execution, Semantic and Compliance Risks in MPLADS Works**

Problem Statement: SIH26102 | Organization: Ministry of Statistics & Programme Implementation (MoSPI) | Division: Data Informatics & Innovation Division (DIID)

---

## What It Does

MPLAD-SHIELD is an AI-assisted risk-intelligence layer over MPLADS (Member of Parliament Local Area Development Scheme) data. It analyzes thousands of development works across India and answers one question: **which projects should a district officer look at first on Monday morning, and why?**

It does NOT detect fraud. It identifies contextual anomalies, ranks projects by investigation priority, and explains every score with auditable evidence.

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MPLAD-SHIELD PIPELINE                        │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ DATA SOURCES │  eSAKSHI public dashboard fields + synthetic corpus
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────┐
  │ 1. DATA INGESTION    │  5,000 synthetic projects + 7 demo cases
  │    & GENERATION      │  12 states, 40 districts, 8 work categories
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 2. CLEANING &        │  Normalize dates/amounts, validate consistency,
  │    NORMALISATION     │  flag missing fields, controlled vocabulary
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 3. FEATURE           │  28 named features across 5 families:
  │    ENGINEERING       │  financial, temporal, execution, payment, compliance
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 4. DETECTION (parallel)                                  │
  │                                                          │
  │  ┌────────────┐ ┌──────────┐ ┌────────────┐ ┌────────┐ │
  │  │ 6 Rules    │ │ Peer     │ │ Isolation  │ │ TF-IDF │ │
  │  │ (R1-R6)    │ │ Baseline │ │ Forest     │ │ Dupli- │ │
  │  │            │ │ Engine   │ │ (anomaly)  │ │ cates  │ │
  │  └─────┬──────┘ └────┬─────┘ └─────┬──────┘ └───┬────┘ │
  │        │              │             │             │      │
  │        └──────────────┴─────────────┴─────────────┘      │
  │                         │                                 │
  └─────────────────────────┼─────────────────────────────────┘
                            │
                   Each detector emits
                   Evidence objects with
                   points + explanations
                            │
                            ▼
  ┌──────────────────────┐
  │ 5. RISK FUSION       │  Capped additive scoring across 6 dimensions
  │    (0-100 score)     │  Score is assembled FROM evidence, not reverse
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 6. EXPLANATION       │  Evidence → ranked human-readable sentences
  │    BUILDER           │  + recommended action + confidence level
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 7. SQLite DATABASE   │  Precomputed scores, evidence, alerts, history
  │    (batch output)    │  The pipeline writes; the API only reads.
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 8. FastAPI SERVICE   │  8 REST endpoints serving scored data
  │    (read-only)       │  + 1 write endpoint for human review
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 9. REACT DASHBOARD   │  5 pages: Overview, Monitoring, Project Detail,
  │    (5 pages)         │  Alerts, Analytics — for 4 stakeholder levels
  └──────────────────────┘
         │
         ▼
  ┌──────────────────────┐
  │ 10. HUMAN REVIEW     │  Official marks case as: valid / false positive /
  │     (in-the-loop)    │  investigate — feedback calibrates future scoring
  └──────────────────────┘
```

---

## Datasets

| Dataset | Source | Size | Purpose |
| --- | --- | --- | --- |
| Synthetic Project Corpus | `generate_corpus.py` (seeded RNG) | 5,000 projects | Realistic MPLADS-like works with proper distributions for peer baselines |
| Demo Scenarios | `scenarios.py` (deterministic) | 7 projects | Handcrafted cases to demonstrate each detection capability |
| Financial Transactions | Generated per project | ~25,000 rows | 3-8 payment installments per project, milestone-aligned |
| Progress Updates | Generated per project | ~30,000 rows | 6 monthly snapshots per project, logistic growth + noise |
| Agencies | Generated | 200 entries | Synthetic implementing agencies with type/district |

### Data Characteristics

- **12 States:** Bihar, UP, MP, Odisha, Rajasthan, Maharashtra, Tamil Nadu, Karnataka, West Bengal, Jharkhand, Chhattisgarh, Gujarat
- **40 Districts:** 3-4 per state
- **8 Work Categories:** Roads, Community Halls, Schools, Hospitals, Water Supply, Drainage, Bridges/Culverts, Solar/Electrical
- **Amount Distributions:** Log-normal per category (roads median ~12L, hospitals ~25L, drainage ~6L)
- **Provenance:** Every record carries a `data_source` flag: `real` | `derived` | `synthetic`

### Why Synthetic?

Real MPLADS data from eSAKSHI is structurally mirrored but not bulk-exportable. Synthetic anomaly injection is the standard validation method when no fraud labels exist. The pipeline ingests any CSV matching the schema — a real export drops in without code changes.

---

## Methods

### 1. Contextual Peer Baselines

Instead of fixed thresholds ("flag anything over 30 lakhs"), each project is compared to **comparable peers**:

- **Group key:** (category, state, cost_band) — fallback to (category, national) if n < 30
- **Statistic:** Median + MAD (Median Absolute Deviation) — robust to the very outliers being detected
- **Output:** Robust z-score = 0.6745 * (x - median) / MAD

A 42L road in Bihar (peer median 12L) is a 3.4-sigma outlier. The same road in a hill state might be perfectly normal.

### 2. Rule-Based Indicators (6 deterministic rules)

| Rule | Detects | Max Points | Method |
| --- | --- | --- | --- |
| R1 | Cost overrun vs peers | 25 | Robust z-score thresholds (z >= 2.0 to 4.0) |
| R2 | Progress-expenditure mismatch | 20 | Gap = utilisation% - progress% (>= 25pp to 55pp) |
| R3 | Extended delay | 12 | Elapsed / peer median duration ratio (> 1.5 to 3.0) |
| R4 | Unusual payment pattern | 18 | Front-loaded + clustered + single-large (3 sub-checks) |
| R5 | Utilisation irregularity | 10 | Expenditure > sanctioned, or completed with < 40% spent |
| R6 | Compliance completeness | 10 | Missing cert, agency, geo-tag, inconsistent dates |

Each rule emits an `Evidence` object containing: points, headline, detail with real numbers, peer context, and confidence.

### 3. Isolation Forest (Unsupervised ML)

- **Purpose:** Catch multivariate anomalies where no single feature crosses a threshold but the combination is rare
- **Features:** 9 scaled numeric (cost_z, utilisation, progress_gap, delay_ratio, payment_count, max_payment_share, payment_gap_std, progress_slope, pct_paid_before_50_progress)
- **Parameters:** n_estimators=200, contamination=0.05, random_state=42
- **Output:** 0-25 points, only awarded above the 90th percentile anomaly score
- **Explainability:** Reports the 3 features furthest from peer median

### 4. Duplicate/Overlap Detection (TF-IDF + Structured Gating)

- **Text similarity:** TF-IDF vectorizer with char (3-5) and word (1-2) n-grams + cosine similarity
- **Gating rules (ALL must hold):**
  - cosine >= 0.72
  - Same district
  - Same category
  - |sanction_date_A - sanction_date_B| <= 180 days
  - 0.6 <= amount_A / amount_B <= 1.67
- **Points:** 15 * min(1, (cosine - 0.72) / 0.20), scaled down 40% if agencies differ
- **Why gating matters:** "Construction of CC road" appears thousands of times legitimately — text similarity alone produces false positives

### 5. Risk Fusion (Capped Additive Model)

Six dimensions with hard caps ensure no single signal dominates:

| Dimension | Cap | Question Answered |
| --- | --- | --- |
| Financial | 25 | Does this cost what comparable works cost? |
| Progress | 20 | Has money moved faster than the work? |
| Payment | 18 | Is money leaving in an unusual rhythm? |
| Duplication | 15 | Might this work already have been funded? |
| Temporal | 12 | Is it late, and getting worse? |
| Compliance | 10 | Is the record itself sound? |
| **Total** | **100** | **Investigation priority — not a verdict** |

### 6. Tier Assignment

| Tier | Score | Target Share | Meaning |
| --- | --- | --- | --- |
| LOW | 0-29 | ~70% | No action. Routine monitoring. |
| MEDIUM | 30-54 | ~20% | Watch list. Re-check next cycle. |
| HIGH | 55-79 | ~8% | Recommended for desk review. |
| CRITICAL | 80-100 | ~2% | Priority field verification. Multiple independent indicators. |

On 5,000 projects: ~100 critical, ~400 high — a queue a district team can actually clear.

### 7. Explanation Builder

Every alert carries human-readable evidence. The score is assembled FROM explanations:

```
PROJECT #MPL-BR-2024-0417 · Construction of CC road, Ward 7, Danapur
RISK SCORE 87 / 100 — CRITICAL · rank 12 of 5,007

+25  Financial · Cost per km is 42.0 L against a peer median of 12.4 L
     for 1,240 comparable road works in Bihar (robust z = 3.4)
+20  Progress · 84% of funds released against 30% reported physical progress
     (gap of 54 percentage points; peer median gap 6 pp)
+18  Payment · 3 releases within 11 days totalling 84% of sanction,
     before the 50% progress milestone
+14  Duplication · 0.89 description similarity to #MPL-BR-2024-0388,
     same district, same agency, sanctioned 41 days apart
+10  Temporal · 214 days past the category's median completion window;
     risk score rose from 52 → 87 over the last two months

RECOMMENDED ACTION · Priority field verification by District Authority
NOTE · Risk indicators are investigation signals, not findings of wrongdoing.
```

### 8. Human-in-the-Loop Review

Officials can mark cases as:
- **Valid** — the alert was justified, investigation warranted
- **False positive** — legitimate explanation exists
- **Investigate** — escalate for field verification

Reviewer feedback becomes the calibration signal for future scoring.

---

## Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | Vite + React 18 + TypeScript + Tailwind CSS v4 + Recharts | Risk dashboard (5 pages) |
| API | FastAPI + Pydantic + Uvicorn | 8 REST endpoints, OpenAPI docs |
| Database | SQLite + SQLAlchemy | Zero-setup, committable, single-file |
| ML Pipeline | pandas + numpy + scikit-learn + scipy + joblib | Feature engineering + detection |
| NLP | scikit-learn TF-IDF | Duplicate description matching |
| Config | YAML | Single source for all thresholds/weights |

### Explicitly Not Used (and why)

| Technology | Reason |
| --- | --- |
| Docker/Kubernetes | Unnecessary for a single-machine demo |
| PostgreSQL/Redis | SQLite is sufficient at 5,000 rows and zero-setup |
| Neural networks/LSTM | Need volume, tuning, GPU time; poor explainability |
| Supervised fraud classifier | No ground-truth fraud labels exist |
| LLM-generated explanations | Non-deterministic, can hallucinate accusations |
| SHAP on fused score | Score is already additive — SHAP would explain arithmetic |

---

## 7 Demo Cases

| # | Project | Score | Tier | What It Demonstrates |
| --- | --- | --- | --- | --- |
| 1 | Anganwadi building, Nalanda | 8 | LOW | Normal project — baseline for comparison |
| 2 | Community hall, Rewa | 44 | MEDIUM | Single signal: cost overrun vs peers |
| 3 | Culvert, Kalahandi | 38 | MEDIUM | Single signal: extended delay + stall |
| 4 | School wall, Jaunpur | 57 | HIGH | Single signal: money ahead of progress |
| 5 | CC road pair, Danapur | 61 | HIGH | Duplicate detection with structured gating |
| 6 | Solar lights, Bhilwara | 64 | HIGH | Payment pattern + ML corroboration |
| 7 | CC road (hero), Danapur | 87 | CRITICAL | All signals converge — the fusion argument |

**The fusion argument:** Case 2 alone is a costly work. Case 4 alone is a reporting lag. Case 5 alone is often a legitimate phased work. But when five independent signals land on the same record, that is not noise — and no single filter can surface it.

---

## Key Design Principles

1. **Scores are precomputed** — the ML pipeline is a batch job that writes to SQLite; the API never calls a model
2. **Rules first, ML second** — 6 deterministic indicators carry 70% of demo value at 15% of the risk
3. **Explanation is first-class** — the score is assembled from evidence, not reverse-engineered from a black box
4. **Language discipline** — "high risk, recommended for review" never "fraud detected" or "guilty"
5. **Context over thresholds** — peer baselines make a 42L road suspicious in one state and normal in another
6. **Human decides** — the system ranks; officials investigate; verdicts are never automated

---

## Novelty

The novelty is NOT Isolation Forest, TF-IDF, or SHAP individually. It is:

> A project-centric, MPLADS-specific risk-intelligence framework that fuses financial, execution, temporal, semantic and compliance evidence into explainable risk profiles and prioritized early-warning cases for human investigation.

Specifically:
- MPLADS lifecycle-specific risk modelling (recommendation → sanction → execution → payment → completion)
- Contextual peer baselines instead of universal fixed thresholds
- Multi-dimensional risk fusion where weak signals reinforce each other
- Temporal trajectory for early warning (catch deterioration before terminal state)
- Semantic + structured duplicate detection (text similarity gated by geography/category/time/cost)
- Explainable investigation packets (the explanation IS the score)
- Human-in-the-loop calibration (not autonomous fraud adjudication)

---

## Validation Strategy

| Method | What It Proves |
| --- | --- |
| Synthetic anomaly injection | Detectors fire on known ground-truth anomalies |
| Precision@20 on injected cases | Fusion ranks injected anomalies in the top 20 |
| Ablation (rules-only vs +IF vs +duplicate) | Each modality adds ranking value |
| E2E test suite (7 scenarios) | Pipeline produces correct tiers and indicators |
| Tier distribution check (~70/20/8/2) | Alert volume is operationally manageable |
| Cross-model agreement (IF + LOF) | Independent detectors corroborate findings |

---

## Dashboard Pages

| Page | Route | Audience | Key Elements |
| --- | --- | --- | --- |
| National Overview | `/` | Ministry | Stat tiles, tier distribution, state risk ranking, critical alerts |
| Risk Monitoring | `/monitor` | State/District | Sortable table, filters, tier chips, pagination |
| Project Detail | `/project/:id` | Investigator | Score panel, evidence list, twin timeline, duplicates, actions |
| Alerts | `/alerts` | District Authority | Severity-grouped queue, recommended actions, disclaimers |
| Analytics | `/analytics` | Analysts | State trends, category rates, scatter plots, indicator frequency |

A role switcher (MP / District / State / Ministry) changes the default scope and labels without separate builds.

---

## One-Line Summary

MPLAD-SHIELD does not detect fraud. It tells a district officer which twelve of five thousand works to look at on Monday morning, and exactly why.
