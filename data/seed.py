"""Seed the SQLite database from generated CSV files."""
import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")
DB_PATH = os.path.join(DB_DIR, "mplad.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")


def seed():
    print("=== MPLAD-SHIELD: Seeding Database ===")

    os.makedirs(DB_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("   Removed existing database")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    print("[1/5] Creating schema...")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    print("[2/5] Loading CSV files...")
    raw_projects = pd.read_csv(os.path.join(DATA_DIR, "raw_projects.csv"))
    raw_txns = pd.read_csv(os.path.join(DATA_DIR, "raw_transactions.csv"))
    raw_progress = pd.read_csv(os.path.join(DATA_DIR, "raw_progress.csv"))
    raw_agencies = pd.read_csv(os.path.join(DATA_DIR, "raw_agencies.csv"))

    demo_projects = pd.read_csv(os.path.join(DATA_DIR, "demo_projects.csv"))
    demo_txns = pd.read_csv(os.path.join(DATA_DIR, "demo_transactions.csv"))
    demo_progress = pd.read_csv(os.path.join(DATA_DIR, "demo_progress.csv"))
    demo_agencies = pd.read_csv(os.path.join(DATA_DIR, "demo_agencies.csv"))

    all_agencies = pd.concat([raw_agencies, demo_agencies]).drop_duplicates(subset=["agency_id"])
    all_projects = pd.concat([raw_projects, demo_projects])
    all_txns = pd.concat([raw_txns, demo_txns])
    all_progress = pd.concat([raw_progress, demo_progress])

    print(f"   Projects: {len(all_projects)} ({len(raw_projects)} synthetic + {len(demo_projects)} demo)")
    print(f"   Transactions: {len(all_txns)}")
    print(f"   Progress updates: {len(all_progress)}")
    print(f"   Agencies: {len(all_agencies)}")

    print("[3/5] Normalizing column names and inserting...")
    col_map = {
        "expected_completion_date": "expected_completion",
        "latitude": "lat",
        "longitude": "lon",
    }
    all_projects.rename(columns={k: v for k, v in col_map.items() if k in all_projects.columns}, inplace=True)
    if "description" not in all_projects.columns:
        all_projects["description"] = all_projects["work_name"]
    if "actual_completion" not in all_projects.columns:
        all_projects["actual_completion"] = None
    if "data_source" not in all_projects.columns:
        all_projects["data_source"] = "synthetic"

    _insert_agencies(conn, all_agencies)
    _insert_projects(conn, all_projects)
    _insert_transactions(conn, all_txns)
    _insert_progress(conn, all_progress)

    print("[4/5] Computing features...")
    from data.features import compute_features

    features_df = compute_features(all_projects, all_txns, all_progress)
    _insert_features(conn, features_df)
    print(f"   {len(features_df)} feature rows computed and inserted")

    print("[5/5] Seeding risk history for demo cases...")
    _seed_demo_history(conn)

    conn.commit()
    conn.close()

    print(f"\n=== Seeding complete: {DB_PATH} ===")
    print(f"   Total projects: {len(all_projects)}")


def _insert_agencies(conn, df):
    cols = ["agency_id", "agency_name", "agency_type", "district", "state"]
    available = [c for c in cols if c in df.columns]
    for _, row in df[available].iterrows():
        values = [row.get(c) for c in available]
        placeholders = ",".join(["?"] * len(available))
        conn.execute(f"INSERT OR IGNORE INTO agencies ({','.join(available)}) VALUES ({placeholders})", values)


def _insert_projects(conn, df):
    cols = [
        "project_id", "work_name", "description", "category", "state", "district",
        "constituency", "mp_name", "agency_id", "sanctioned_amount", "sanction_date",
        "expected_completion", "actual_completion", "status", "lat", "lon",
        "has_completion_cert", "data_source", "fiscal_year"
    ]
    available = [c for c in cols if c in df.columns]
    for _, row in df.iterrows():
        values = [row.get(c) if pd.notna(row.get(c)) else None for c in available]
        placeholders = ",".join(["?"] * len(available))
        conn.execute(f"INSERT OR IGNORE INTO projects ({','.join(available)}) VALUES ({placeholders})", values)


def _insert_transactions(conn, df):
    cols = ["txn_id", "project_id", "txn_date", "amount", "txn_type", "milestone_progress_at_payment"]
    available = [c for c in cols if c in df.columns]
    for _, row in df.iterrows():
        values = [row.get(c) if pd.notna(row.get(c)) else None for c in available]
        placeholders = ",".join(["?"] * len(available))
        conn.execute(f"INSERT OR IGNORE INTO financial_transactions ({','.join(available)}) VALUES ({placeholders})", values)


def _insert_progress(conn, df):
    cols = ["update_id", "project_id", "update_date", "progress_pct", "reported_by", "remarks"]
    available = [c for c in cols if c in df.columns]
    for _, row in df.iterrows():
        values = [row.get(c) if pd.notna(row.get(c)) else None for c in available]
        placeholders = ",".join(["?"] * len(available))
        conn.execute(f"INSERT OR IGNORE INTO progress_updates ({','.join(available)}) VALUES ({placeholders})", values)


def _insert_features(conn, features_df):
    features_df = features_df.reset_index()
    cols = features_df.columns.tolist()
    for _, row in features_df.iterrows():
        values = [row[c] if pd.notna(row[c]) else None for c in cols]
        placeholders = ",".join(["?"] * len(cols))
        conn.execute(f"INSERT OR REPLACE INTO features ({','.join(cols)}) VALUES ({placeholders})", values)


def _seed_demo_history(conn):
    """Seed risk history snapshots for demo cases to show trajectory."""
    histories = {
        "MPL-BR-2024-0417": [
            ("2024-03-01", 32), ("2024-04-01", 45), ("2024-05-01", 52),
            ("2024-06-01", 68), ("2024-07-01", 78), ("2024-08-01", 87),
        ],
        "MPL-RJ-2024-0620": [
            ("2024-03-01", 15), ("2024-04-01", 22), ("2024-05-01", 35),
            ("2024-06-01", 48), ("2024-07-01", 56), ("2024-08-01", 64),
        ],
        "MPL-UP-2024-0455": [
            ("2024-03-01", 12), ("2024-04-01", 25), ("2024-05-01", 38),
            ("2024-06-01", 45), ("2024-07-01", 50), ("2024-08-01", 57),
        ],
    }
    for pid, snapshots in histories.items():
        for date, score in snapshots:
            conn.execute(
                "INSERT OR REPLACE INTO risk_history (project_id, snapshot_date, total_score) VALUES (?,?,?)",
                (pid, date, score)
            )


if __name__ == "__main__":
    seed()
