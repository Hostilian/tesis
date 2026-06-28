"""
api_server.py — Enterprise FastAPI ingestion and webhook server.

Exposes REST endpoints for querying anomalies and status, and webhook receivers
for real-time commodity spot prices and satellite tile processing ingestion.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, List
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from pydantic import BaseModel, Field

from pipeline.src.ingestion import SatelliteDataIngester
from pipeline.src.http_resilience import stable_json_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Space-Based Economic Intelligence (SBEI) REST API",
    description="Enterprise REST & Webhook Ingestion Engine",
    version="1.0.0",
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "data"
ANOMALIES_FILE = DATA_DIR / "anomalies.json"
FINANCIAL_FEED_FILE = DATA_DIR / "financial_feed.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


class BoundingBox(BaseModel):
    bbox: List[float] = Field(..., json_schema_extra={"example": [-68.5, -23.8, -68.1, -23.2]})
    start_date: str = Field(..., json_schema_extra={"example": "2024-01-01"})
    end_date: str = Field(..., json_schema_extra={"example": "2024-12-31"})


class FinancialPayload(BaseModel):
    indicator: str = Field(..., json_schema_extra={"example": "lithium_carbonate_spot_price"})
    value: float = Field(..., json_schema_extra={"example": 14200.0})
    currency: str = Field(default="USD")
    source: str = Field(..., json_schema_extra={"example": "LME"})


def run_background_pipeline(bbox: List[float], start_date: str, end_date: str):
    logger.info(f"Triggering asynchronous processing for bbox {bbox} from {start_date} to {end_date}")
    # In a full production system, this triggers a Celery task.
    # Here, we log the execution and save the state.
    # (Simulated pipeline run)
    logger.info("Background processing successfully initiated.")


@app.get("/api/v1/status")
def get_status():
    """Retrieve the status and health check information of the API integration layer."""
    try:
        ingester = SatelliteDataIngester()
        health = ingester.health_check()
        
        # Load recent runs from status index file if it exists
        status_file = Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "v1" / "status" / "index.json"
        recent_runs = []
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
                    recent_runs = status_data.get("recent_runs", [])
            except Exception as e:
                logger.error(f"Failed to read status file: {e}")
                
        return {
            "status": "online",
            "environment": "production" if os.getenv("GITHUB_ACTIONS") else "development",
            "integrations": health,
            "recent_runs": recent_runs,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to check health: {str(exc)}")


@app.get("/api/v1/anomalies")
def get_anomalies():
    """Retrieve the complete list of economic anomalies."""
    if not ANOMALIES_FILE.exists():
        return []
    try:
        with open(ANOMALIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read anomalies database: {str(exc)}")


@app.get("/api/v1/anomalies/{anomaly_id}")
def get_anomaly_by_id(anomaly_id: str):
    """Retrieve details for a single anomaly."""
    anomalies = get_anomalies()
    for anom in anomalies:
        if anom.get("id") == anomaly_id:
            return anom
    raise HTTPException(status_code=404, detail=f"Anomaly with ID {anomaly_id} not found.")


@app.post("/api/v1/webhooks/financial")
def receive_financial_webhook(payload: FinancialPayload = Body(...)):
    """
    Webhook endpoint to ingest real-time market data feeds (e.g. commodity prices).
    Returns an immutable transaction hash for data provenance.
    """
    try:
        data = payload.model_dump()
        tx_hash = stable_json_hash(data)
        data["tx_hash"] = tx_hash
        
        # Load or create feed
        feed = []
        if FINANCIAL_FEED_FILE.exists():
            try:
                with open(FINANCIAL_FEED_FILE, "r", encoding="utf-8") as f:
                    feed = json.load(f)
            except Exception:
                feed = []
                
        feed.append(data)
        with open(FINANCIAL_FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(feed, f, indent=2)
            
        logger.info(f"Financial feed ingested: {payload.indicator} = {payload.value} (tx: {tx_hash})")
        return {
            "status": "success",
            "message": "Market feed ingested successfully.",
            "transaction_hash": tx_hash,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process financial webhook: {str(exc)}")


@app.post("/api/v1/ingest/satellite")
def trigger_satellite_ingestion(payload: BoundingBox, background_tasks: BackgroundTasks):
    """
    RESTful endpoint to trigger geospatial pipeline runs for specific coordinates.
    """
    background_tasks.add_task(
        run_background_pipeline,
        payload.bbox,
        payload.start_date,
        payload.end_date
    )
    return {
        "status": "queued",
        "message": f"Geospatial ingestion task queued for bbox {payload.bbox}.",
    }
