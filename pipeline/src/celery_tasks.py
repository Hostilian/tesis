"""
celery_tasks.py — Distributed task definition module.

Defines asynchronous processing tasks for satellite tile retrieval and anomaly detection.
Uses Redis as the default message broker.
"""

from __future__ import annotations

import logging
import os
from celery import Celery

from pipeline.src.ingestion import SatelliteDataIngester
from pipeline.src.preprocessing import GeospatialPreprocessor
from pipeline.src.anomaly_detector import SatelliteAnomalyOrchestrator
from pipeline.src.exporter import GeospatialExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Celery application
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "sbei_tasks",
    broker=broker_url,
    backend=result_backend,
)

# Configuration overrides
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 minutes maximum runtime per tile
)


@celery_app.task(name="pipeline.src.celery_tasks.process_satellite_tile_task", bind=True, max_retries=3)
def process_satellite_tile_task(self, bbox: list[float], start_date: str, end_date: str, region_id: str) -> dict:
    """
    Asynchronously run the spatial anomaly detection pipeline for a bounding box.
    Retries automatically on transient resource failures.
    """
    logger.info(f"Worker processing tile: {region_id} (BBox: {bbox})")
    
    try:
        # Initialize pipeline components inside the worker context
        ingester = SatelliteDataIngester()
        preprocessor = GeospatialPreprocessor()
        orchestrator = SatelliteAnomalyOrchestrator()
        exporter = GeospatialExporter()
        
        # Authenticate GEE or fall back to mock
        ingester.authenticate_gee()
        
        # Fetch bands
        bands = ingester.fetch_sentinel2_data(bbox, start_date, end_date)
        processed = preprocessor.process_raw_bands(bands)
        
        # Run detection
        features, coords = preprocessor.prepare_ml_features(processed)
        result = orchestrator.run_spatial_detection(bands, region_id, date_acquired=end_date)
        
        logger.info(f"Worker complete. Status: {result.get('skipped_reason') or 'ANOMALIES_PROCESSED'}")
        return {
            "region_id": region_id,
            "status": "success",
            "anomalous_pixel_count": result.get("anomalous_pixel_count", 0),
            "valid_pixel_count": result.get("valid_pixel_count", 0),
            "confidence_mean": result.get("confidence_mean", 0.0),
        }
        
    except Exception as exc:
        logger.error(f"Task failed on tile {region_id}: {str(exc)}")
        # Exponential backoff retry logic for celery tasks
        retry_delay = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=retry_delay)
