"""
Synthetic Data Generator for MPLAD-SHIELD
==========================================
Generates 5,000 MPLADS-like project records with realistic distributions
for amounts, durations, payments, and progress snapshots.

Usage:
    python data/generate_corpus.py

Output:
    data/raw_projects.csv
    data/raw_transactions.csv
    data/raw_progress.csv
    data/raw_agencies.csv
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
N_PROJECTS = 5000
OUTPUT_DIR = Path(__file__).resolve().parent

# Reproducible RNG
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

STATES_DISTRICTS = {
    "Bihar": ["Patna", "Nalanda", "Gaya", "Muzaffarpur"],
    "Uttar Pradesh": ["Lucknow", "Jaunpur", "Varanasi", "Allahabad"],
    "Madhya Pradesh": ["Bhopal", "Rewa", "Indore", "Jabalpur"],
    "Odisha": ["Bhubaneswar", "Kalahandi", "Cuttack", "Puri"],
    "Rajasthan": ["Jaipur", "Bhilwara", "Jodhpur", "Udaipur"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Tamil Nadu": ["Chennai", "Madurai", "Coimbatore"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubli"],
    "West Bengal": ["Kolkata", "Howrah", "Darjeeling"],
    "Jharkhand": ["Ranchi", "Dhanbad", "Jamshedpur"],
    "Chhattisgarh": ["Raipur", "Bilaspur", "Durg"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
}

STATE_CODES = {
    "Bihar": "BR",
    "Uttar Pradesh": "UP",
    "Madhya Pradesh": "MP",
    "Odisha": "OD",
    "Rajasthan": "RJ",
    "Maharashtra": "MH",
    "Tamil Nadu": "TN",
    "Karnataka": "KA",
    "West Bengal": "WB",
    "Jharkhand": "JH",
    "Chhattisgarh": "CG",
    "Gujarat": "GJ",
}

# Approximate lat/lon bounding boxes per state (min_lat, max_lat, min_lon, max_lon)
STATE_BOUNDS = {
    "Bihar": (24.5, 27.5, 83.5, 88.0),
    "Uttar Pradesh": (24.0, 30.5, 77.0, 84.5),
    "Madhya Pradesh": (21.5, 26.5, 74.0, 82.5),
    "Odisha": (18.0, 22.5, 81.5, 87.5),
    "Rajasthan": (23.0, 30.0, 69.5, 78.0),
    "Maharashtra": (15.5, 22.0, 72.5, 80.5),
    "Tamil Nadu": (8.0, 13.5, 76.0, 80.5),
    "Karnataka": (11.5, 18.5, 74.0, 78.5),
    "West Bengal": (21.5, 27.0, 86.5, 89.5),
    "Jharkhand": (22.0, 25.5, 83.5, 87.5),
    "Chhattisgarh": (18.0, 24.0, 80.0, 84.5),
    "Gujarat": (20.0, 24.5, 68.0, 74.5),
}

CATEGORIES = [
    "Roads",
    "Community Halls",
    "Schools",
    "Hospitals",
    "Water Supply",
    "Drainage",
    "Bridges and Culverts",
    "Solar and Electrical",
]

# Log-normal parameters: median in lakhs, sigma for spread
# median = exp(mu), so mu = ln(median_lakhs)
CATEGORY_AMOUNT_PARAMS = {
    "Roads": (12.0, 0.35),
    "Community Halls": (11.0, 0.30),
    "Schools": (18.0, 0.30),
    "Hospitals": (25.0, 0.35),
    "Water Supply": (8.0, 0.30),
    "Drainage": (6.0, 0.30),
    "Bridges and Culverts": (15.0, 0.35),
    "Solar and Electrical": (10.0, 0.30),
}

# Duration in months: (mean, std)
CATEGORY_DURATION = {
    "Roads": (8, 2),
    "Community Halls": (12, 3),
    "Schools": (12, 3),
    "Hospitals": (14, 3),
    "Water Supply": (6, 2),
    "Drainage": (5, 1.5),
    "Bridges and Culverts": (14, 3),
    "Solar and Electrical": (6, 2),
}

WORK_NAME_TEMPLATES = {
    "Roads": [
        "Construction of CC road in Ward {ward}, {district}",
        "Repair and widening of village road near {district}",
        "Construction of bituminous road, {district}",
        "Black-topping of road from village to highway, {district}",
    ],
    "Community Halls": [
        "Construction of community hall, {district}",
        "Construction of Anganwadi building, Ward {ward}, {district}",
        "Panchayat Bhawan construction, {district}",
        "Construction of multi-purpose community center, {district}",
    ],
    "Schools": [
        "Construction of school boundary wall, {district}",
        "Additional classroom construction, Govt School, {district}",
        "Toilet block construction, Primary School, {district}",
        "Construction of school building, {district}",
    ],
    "Hospitals": [
        "Construction of PHC building, {district}",
        "Extension of sub-district hospital, {district}",
        "Construction of Ayushman Bhawan, {district}",
        "Renovation of community health centre, {district}",
    ],
    "Water Supply": [
        "Boring and hand-pump installation, {district}",
        "Overhead water tank construction, {district}",
        "Water pipeline laying in Ward {ward}, {district}",
        "Tube-well and pump-house construction, {district}",
    ],
    "Drainage": [
        "Construction of pucca drain, Ward {ward}, {district}",
        "Storm water drainage system, {district}",
        "Open drain to covered drain conversion, {district}",
        "Nallah widening and channelization, {district}",
    ],
    "Bridges and Culverts": [
        "Construction of culvert on village road, {district}",
        "RCC bridge over nallah, {district}",
        "Box culvert construction, {district}",
        "Foot-over bridge construction, {district}",
    ],
    "Solar and Electrical": [
        "Installation of solar street lights, {district}",
        "Solar panel installation at Panchayat Bhawan, {district}",
        "LED street light installation, Ward {ward}, {district}",
        "Electrification of village road, {district}",
    ],
}

FISCAL_YEARS = ["2022-23", "2023-24", "2024-25"]

# Fiscal year date ranges (April to March)
FY_RANGES = {
    "2022-23": (datetime(2022, 4, 1), datetime(2023, 3, 31)),
    "2023-24": (datetime(2023, 4, 1), datetime(2024, 3, 31)),
    "2024-25": (datetime(2024, 4, 1), datetime(2025, 3, 31)),
}


def generate_agency_names(n=200):
    """Generate synthetic agency names."""
    prefixes = [
        "Agarwal", "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Verma",
        "Mishra", "Yadav", "Jha", "Sahu", "Reddy", "Nair", "Pillai",
        "Das", "Roy", "Chatterjee", "Banerjee", "Rao", "Iyer",
        "National", "Supreme", "Royal", "Prime", "Excel", "Star",
        "Diamond", "Golden", "Silver", "Apex", "Metro", "Urban",
        "Global", "Modern", "Future", "Progressive", "United", "Allied",
        "Pioneer", "Sunrise", "Horizon", "Zenith", "Summit", "Pinnacle",
        "Elite", "Premier", "Pacific", "Atlantic", "Sahara", "Ganges",
    ]
    suffixes = [
        "Construction", "Infrastructure", "Builders", "Enterprises",
        "Engineering", "Constructions Pvt Ltd", "Associates",
        "Projects", "Works", "Developers", "Contractors",
        "Civil Works", "Building Solutions", "Infra Pvt Ltd",
    ]

    names = set()
    while len(names) < n:
        prefix = rng.choice(prefixes)
        suffix = rng.choice(suffixes)
        names.add(f"{prefix} {suffix}")
    return sorted(names)


def generate_sanction_date(fy: str) -> datetime:
    """Generate a random sanction date within a fiscal year."""
    start, end = FY_RANGES[fy]
    days_in_range = (end - start).days
    offset = int(rng.integers(0, days_in_range))
    return start + timedelta(days=offset)


def generate_amount(category: str) -> float:
    """Generate sanctioned amount (in lakhs) using log-normal distribution."""
    median, sigma = CATEGORY_AMOUNT_PARAMS[category]
    mu = np.log(median)
    amount = float(rng.lognormal(mu, sigma))
    return round(amount, 2)


def generate_duration(category: str) -> int:
    """Generate expected duration in months."""
    mean, std = CATEGORY_DURATION[category]
    duration = int(rng.normal(mean, std))
    return max(3, duration)  # minimum 3 months


def generate_payments(project_id: str, sanctioned_amount: float,
                      sanction_date: datetime, duration_months: int,
                      progress_final: float) -> list:
    """Generate 3-8 payment installments roughly aligned to milestones."""
    n_payments = int(rng.integers(3, 9))
    # Distribute amounts using Dirichlet
    proportions = rng.dirichlet(np.ones(n_payments) * 2)
    # Scale to released amount (progress_final fraction of sanctioned)
    released_fraction = min(progress_final / 100.0 + rng.uniform(0, 0.1), 1.0)
    total_released = sanctioned_amount * released_fraction

    amounts = proportions * total_released
    amounts = np.round(amounts, 2)

    # Generate dates spread across the project duration
    max_days = duration_months * 30
    offsets = sorted(rng.integers(7, max(max_days, 30), size=n_payments))

    payments = []
    cumulative_progress = 0
    for i, (amt, offset) in enumerate(zip(amounts, offsets)):
        txn_date = sanction_date + timedelta(days=int(offset))
        cumulative_progress = min(100, cumulative_progress + (100 / n_payments) * rng.uniform(0.7, 1.3))
        payments.append({
            "txn_id": f"TXN-{project_id}-{i+1:02d}",
            "project_id": project_id,
            "txn_date": txn_date.strftime("%Y-%m-%d"),
            "amount": float(amt),
            "txn_type": "Release",
            "milestone_progress_at_payment": round(min(100, cumulative_progress), 1),
        })

    return payments


def logistic_growth(t, L=100, k=0.5, t0=3):
    """Logistic growth function for progress."""
    return L / (1 + np.exp(-k * (t - t0)))


def generate_progress_snapshots(project_id: str, sanction_date: datetime,
                                 duration_months: int, final_progress: float) -> list:
    """Generate 6 monthly progress snapshots following logistic growth."""
    snapshots = []
    # Scale logistic curve to reach final_progress
    t_values = np.linspace(0, 6, 6)
    raw_progress = logistic_growth(t_values, L=final_progress, k=1.0, t0=3)

    for i in range(6):
        noise = rng.normal(0, 2)
        progress = max(0, min(100, raw_progress[i] + noise))
        update_date = sanction_date + timedelta(days=30 * (i + 1))
        snapshots.append({
            "update_id": f"UPD-{project_id}-{i+1:02d}",
            "project_id": project_id,
            "update_date": update_date.strftime("%Y-%m-%d"),
            "progress_pct": round(progress, 1),
        })

    return snapshots


def determine_status(progress: float) -> str:
    """Determine project status based on final progress."""
    if progress >= 95:
        return "Completed"
    elif progress > 5:
        return "In Progress"
    else:
        return "Not Started"


def generate_corpus():
    """Generate the full synthetic corpus of 5000 projects."""
    print("Generating synthetic MPLADS corpus...")
    print(f"  Seed: {SEED}")
    print(f"  Projects: {N_PROJECTS}")

    # Generate agencies
    agency_names = generate_agency_names(200)
    agencies_data = []
    for i, name in enumerate(agency_names):
        state = rng.choice(list(STATES_DISTRICTS.keys()))
        agencies_data.append({
            "agency_id": f"AGY-SYN-{i+1:04d}",
            "agency_name": name,
            "registration_state": state,
            "registration_year": int(rng.integers(2005, 2023)),
            "category": rng.choice(["A", "B", "C"]),
        })

    all_projects = []
    all_transactions = []
    all_progress = []

    # Flatten state-district pairs
    state_district_pairs = []
    for state, districts in STATES_DISTRICTS.items():
        for district in districts:
            state_district_pairs.append((state, district))

    for i in range(N_PROJECTS):
        # Select random state and district
        state, district = state_district_pairs[int(rng.integers(0, len(state_district_pairs)))]
        state_code = STATE_CODES[state]

        # Project ID
        project_id = f"MPL-SYN-{state_code}-{i+1:04d}"

        # Category
        category = rng.choice(CATEGORIES)

        # Work name
        template = rng.choice(WORK_NAME_TEMPLATES[category])
        ward = int(rng.integers(1, 20))
        work_name = template.format(ward=ward, district=district)

        # Fiscal year
        fy = rng.choice(FISCAL_YEARS)
        sanction_date = generate_sanction_date(fy)

        # Amount
        sanctioned_amount = generate_amount(category)

        # Duration
        duration_months = generate_duration(category)
        expected_completion = sanction_date + timedelta(days=duration_months * 30)

        # Final progress
        # Bias toward completion for older projects
        if fy == "2022-23":
            final_progress = float(rng.beta(8, 2) * 100)
        elif fy == "2023-24":
            final_progress = float(rng.beta(5, 3) * 100)
        else:
            final_progress = float(rng.beta(3, 4) * 100)

        final_progress = round(min(100, max(0, final_progress)), 1)

        # Status
        status = determine_status(final_progress)
        has_completion_cert = 1 if status == "Completed" else 0

        # Agency
        agency = rng.choice(agencies_data)

        # Lat/Lon
        bounds = STATE_BOUNDS[state]
        lat = float(rng.uniform(bounds[0], bounds[1]))
        lon = float(rng.uniform(bounds[2], bounds[3]))

        # MP name (synthetic)
        mp_name = f"MP_{state_code}_{int(rng.integers(1, 20)):02d}"

        project = {
            "project_id": project_id,
            "work_name": work_name,
            "category": category,
            "state": state,
            "district": district,
            "fiscal_year": fy,
            "sanction_date": sanction_date.strftime("%Y-%m-%d"),
            "sanctioned_amount": sanctioned_amount,
            "expected_duration_months": duration_months,
            "expected_completion_date": expected_completion.strftime("%Y-%m-%d"),
            "status": status,
            "final_progress_pct": final_progress,
            "has_completion_cert": has_completion_cert,
            "agency_id": agency["agency_id"],
            "agency_name": agency["agency_name"],
            "mp_name": mp_name,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
        }
        all_projects.append(project)

        # Generate payments
        payments = generate_payments(
            project_id, sanctioned_amount, sanction_date,
            duration_months, final_progress
        )
        all_transactions.extend(payments)

        # Generate progress snapshots
        snapshots = generate_progress_snapshots(
            project_id, sanction_date, duration_months, final_progress
        )
        all_progress.extend(snapshots)

    # Create DataFrames
    projects_df = pd.DataFrame(all_projects)
    transactions_df = pd.DataFrame(all_transactions)
    progress_df = pd.DataFrame(all_progress)
    agencies_df = pd.DataFrame(agencies_data)

    return projects_df, transactions_df, progress_df, agencies_df


def save_and_report(projects_df, transactions_df, progress_df, agencies_df):
    """Save CSVs and print summary statistics."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    projects_df.to_csv(OUTPUT_DIR / "raw_projects.csv", index=False)
    transactions_df.to_csv(OUTPUT_DIR / "raw_transactions.csv", index=False)
    progress_df.to_csv(OUTPUT_DIR / "raw_progress.csv", index=False)
    agencies_df.to_csv(OUTPUT_DIR / "raw_agencies.csv", index=False)

    print(f"\n{'='*60}")
    print("MPLAD-SHIELD Synthetic Corpus Generated")
    print(f"{'='*60}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nFiles:")
    print(f"  raw_projects.csv      : {len(projects_df):,} rows")
    print(f"  raw_transactions.csv  : {len(transactions_df):,} rows")
    print(f"  raw_progress.csv      : {len(progress_df):,} rows")
    print(f"  raw_agencies.csv      : {len(agencies_df):,} rows")

    print(f"\n--- Project Summary ---")
    print(f"  States: {projects_df['state'].nunique()}")
    print(f"  Districts: {projects_df['district'].nunique()}")
    print(f"  Categories: {projects_df['category'].nunique()}")
    print(f"  Fiscal Years: {projects_df['fiscal_year'].unique().tolist()}")
    print(f"\n  Status distribution:")
    for status, count in projects_df['status'].value_counts().items():
        print(f"    {status}: {count} ({count/len(projects_df)*100:.1f}%)")

    print(f"\n  Amount statistics (in Lakhs):")
    for cat in CATEGORIES:
        cat_amounts = projects_df[projects_df['category'] == cat]['sanctioned_amount']
        print(f"    {cat:25s}: median={cat_amounts.median():.1f}L, "
              f"mean={cat_amounts.mean():.1f}L, n={len(cat_amounts)}")

    print(f"\n  Agencies: {agencies_df['agency_id'].nunique()}")
    print(f"  Avg payments per project: "
          f"{len(transactions_df)/len(projects_df):.1f}")
    print(f"  Progress snapshots per project: "
          f"{len(progress_df)/len(projects_df):.1f}")


if __name__ == "__main__":
    projects_df, transactions_df, progress_df, agencies_df = generate_corpus()
    save_and_report(projects_df, transactions_df, progress_df, agencies_df)
    print("\nDone.")
