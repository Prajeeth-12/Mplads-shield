"""API smoke tests using FastAPI TestClient."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_overview():
    r = client.get("/api/overview")
    assert r.status_code == 200
    data = r.json()
    assert "total_projects" in data
    assert "tier_counts" in data
    assert "state_risk" in data


def test_projects_list():
    r = client.get("/api/projects?page=1&size=10")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data


def test_project_detail():
    r = client.get("/api/projects/MPL-BR-2024-0417")
    assert r.status_code == 200
    data = r.json()
    assert "project" in data
    assert "score" in data
    assert "evidence" in data
    assert "explanation" in data


def test_alerts():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_analytics():
    r = client.get("/api/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "state_risk" in data
    assert "category_anomaly_rate" in data


def test_similar():
    r = client.get("/api/projects/MPL-BR-2024-0417/similar")
    assert r.status_code == 200


def test_review_post():
    r = client.post("/api/projects/MPL-BR-2024-0417/review", json={
        "verdict": "investigate",
        "reviewer_role": "District Authority",
        "note": "Test review",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["verdict"] == "investigate"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "MPLAD-SHIELD"
