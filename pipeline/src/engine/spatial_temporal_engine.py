"""
spatial_temporal_engine.py — Proprietary Core Spatial-Temporal Economic Engine.

This module contains the decoupled, highly optimized mathematical models for
SBEI's dual spatial-temporal anomaly detection pipeline.

Mathematical Model:
    1. Spatial Outlier Isolation (Ensemble Isolation Forest):
       Isolates anomalies by randomly selecting a feature and a split value,
       building isolation trees (iTrees). Outliers have shorter path lengths:
       s(x, n) = 2^(- E(h(x)) / c(n))
    2. Temporal Deseasonalized Night-Time Lights (NTL) Deviation:
       Z_t = (Y_t - μ_w) / σ_w
       where w is the rolling window baseline and σ_w is bounded to prevent divide-by-zero.
"""

from __future__ import annotations

import logging
import numpy as np
from sklearn.ensemble import IsolationForest

from pipeline.src.utils import calculate_temporal_zscores

logger = logging.getLogger(__name__)


class SpatialTemporalEconomicEngine:
    """
    Decoupled proprietary engine for executing high-throughput economic anomaly detection
    using joint spatial-temporal satellite data models.
    """

    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        """
        Args:
            contamination: Expected fraction of anomalous samples.
            random_state: Seed for reproducibility (typically 42).
        """
        self.contamination = contamination
        self.random_state = random_state
        self.spatial_model: IsolationForest | None = None

    def fit_predict_spatial(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Fits an Isolation Forest to multivariate spatial spectral features
        (typically NDVI, NDWI, and BSI) and computes outlier labels and scores.

        Args:
            features: 2D array of shape (N_pixels, D_features).

        Returns:
            predictions: 1D array of shape (N_pixels,) where -1 is anomaly, 1 is normal.
            scores: 1D array of shape (N_pixels,) of normalized anomaly scores in [0, 1].
        """
        logger.info(
            "Proprietary Engine: Fitting Isolation Forest ensemble (n_estimators=100) on %d samples",
            features.shape[0]
        )
        self.spatial_model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
        )

        predictions = self.spatial_model.fit_predict(features)
        raw_scores = self.spatial_model.decision_function(features)

        # Normalize raw decision function scores into [0, 1] range
        # where 1.0 represents highest anomaly certainty
        min_raw, max_raw = raw_scores.min(), raw_scores.max()
        if max_raw == min_raw:
            scores = np.zeros_like(raw_scores)
        else:
            scores = 1.0 - ((raw_scores - min_raw) / (max_raw - min_raw))

        logger.info("Proprietary Engine: Spatial Isolation Forest fitting completed successfully.")
        return predictions, scores

    def detect_temporal_ntl(self, radiance_series: list[float], rolling_window: int = 12) -> list[float]:
        """
        Computes rolling Z-score anomalies over a night-time lights time series
        to detect sudden, atypical changes in local economic output.

        Args:
            radiance_series: 1D series of nocturnal radiance values.
            rolling_window: Window size for calculating historical mean/std.

        Returns:
            List of Z-scores representing temporal deviations.
        """
        logger.info(
            "Proprietary Engine: Computing rolling Z-score anomalies for time-series (n=%d, window=%d)",
            len(radiance_series), rolling_window
        )
        values = np.array(radiance_series, dtype=float)
        z_scores = calculate_temporal_zscores(values, rolling_window)
        return z_scores.tolist()
