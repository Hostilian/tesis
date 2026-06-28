"""
test_api_server.py — Integration and contract validation tests for the SBEI REST API.
"""

from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from pipeline.src.api_server import app, DATA_DIR, ANOMALIES_FILE, FINANCIAL_FEED_FILE


@pytest.fixture
def client():
    return TestClient(app)


def test_api_status_endpoint(client):
    """GET /api/v1/status must return a valid status schema."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "environment" in data
    assert "integrations" in data
    assert isinstance(data["integrations"], list)
    assert "recent_runs" in data
    assert isinstance(data["recent_runs"], list)
    # Validate structure of runs if present
    for run in data["recent_runs"]:
        assert "run_id" in run
        assert "completed_at" in run
        assert "anomalies_produced" in run
        if "signature" in run:
            assert len(run["signature"]) == 64


def test_api_anomalies_endpoint(client):
    """GET /api/v1/anomalies must return the anomalies list."""
    response = client.get("/api/v1/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_anomalies_by_id_endpoint_not_found(client):
    """GET /api/v1/anomalies/{anomaly_id} returns 404 for unknown ID."""
    response = client.get("/api/v1/anomalies/unknown_id_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_financial_webhook(client):
    """POST /api/v1/webhooks/financial must successfully ingest market data and return combined provenance hash."""
    payload = {
        "indicator": "lithium_carbonate_spot_price",
        "value": 14200.0,
        "currency": "USD",
        "source": "LME"
    }
    response = client.post("/api/v1/webhooks/financial", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "transaction_hash" in data
    assert len(data["transaction_hash"]) == 64  # SHA-256 length


def test_api_satellite_ingest_endpoint(client):
    """POST /api/v1/ingest/satellite queues background task."""
    payload = {
        "bbox": [-68.5, -23.8, -68.1, -23.2],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    response = client.post("/api/v1/ingest/satellite", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "bbox" in data["message"]
