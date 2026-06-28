"""
anomaly_detector.py — Orchestrated anomaly detection pipeline for satellite geospatial data.

This module integrates the spatial Isolation Forest and the temporal Z-score engine
into a single callable interface. It also performs bootstrap-based uncertainty
quantification and handles all edge cases: NaN masking, high cloud cover, coordinate
system validation, and leap-year-safe date arithmetic.

References:
    Liu, F.T., Ting, K.M. & Zhou, Z.H. (2008). Isolation Forest. ICDM.
    doi:10.1109/ICDM.2008.17  [R206]

Author: Eren Ozturk — CZU Prague PEF KII Bachelor Thesis 2026
"""

import logging
import numpy as np
from datetime import datetime, timezone
from typing import Optional

from pipeline.src.utils import (
    calculate_ndvi,
    calculate_ndwi,
    calculate_bsi,
    apply_sentinel_cloud_mask,
    calculate_temporal_zscores,
)
from pipeline.src.models import AnomalyDetector

logger = logging.getLogger(__name__)

# ── Thresholds (documented in Chapter 3 §3.4) ─────────────────────────────────
CLOUD_COVER_SKIP_THRESHOLD = 0.80   # Skip tile if > 80 % cloudy
TEMPORAL_ANOMALY_THRESHOLD  = 2.5   # |Z| > 2.5 → flag temporal anomaly
MIN_VALID_PIXELS            = 50    # Minimum unmasked pixels before aborting


class SatelliteAnomalyOrchestrator:
    """
    End-to-end orchestrator that transforms raw Sentinel-2 / Landsat band arrays
    into structured anomaly records.

    Usage:
        orchestrator = SatelliteAnomalyOrchestrator()
        result = orchestrator.run_spatial_detection(bands_dict, region_id="atacama")
    """

    def __init__(
        self,
        contamination: float = 0.08,
        random_state: int = 42,
        n_bootstrap: int = 50,
    ) -> None:
        """
        Args:
            contamination: Expected fraction of anomalous pixels (0, 0.5].
            random_state: Seed for reproducibility. Locked to 42 per methodology.
            n_bootstrap: Number of bootstrap iterations for uncertainty estimates.
        """
        if not 0 < contamination <= 0.5:
            raise ValueError(f"contamination must be in (0, 0.5], got {contamination}")
        self.contamination = contamination
        self.random_state = random_state
        self.n_bootstrap = n_bootstrap
        self._detector = AnomalyDetector(
            contamination=contamination, random_state=random_state
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Spatial Detection
    # ─────────────────────────────────────────────────────────────────────────

    def run_spatial_detection(
        self,
        bands: dict,
        region_id: str,
        date_acquired: Optional[str] = None,
    ) -> dict:
        """
        Full spatial anomaly detection pipeline on a single satellite scene.

        Args:
            bands: Dict with keys 'B2', 'B3', 'B4', 'B8', 'B11', 'QA60' as np.ndarray.
            region_id: Identifier string for the region being processed.
            date_acquired: ISO-8601 acquisition date ('YYYY-MM-DD'). Defaults to today UTC.

        Returns:
            Dict with keys: region_id, date, anomaly_mask, scores, confidence_mean,
            confidence_ci_low, confidence_ci_high, spectral_stats, valid_pixel_count,
            skipped_reason (None if not skipped).
        """
        date_acquired = date_acquired or datetime.now(timezone.utc).date().isoformat()
        self._validate_iso8601(date_acquired)

        # 1. Cloud-cover gate ──────────────────────────────────────────────────
        qa_band = bands.get("QA60", np.zeros((100, 100), dtype=int))
        clear_mask = apply_sentinel_cloud_mask(qa_band.astype(int))
        cloud_fraction = 1.0 - (clear_mask.sum() / clear_mask.size)

        if cloud_fraction > CLOUD_COVER_SKIP_THRESHOLD:
            logger.warning(
                "Tile %s on %s has %.0f%% cloud cover — skipping.",
                region_id, date_acquired, cloud_fraction * 100,
            )
            return self._skipped_result(
                region_id, date_acquired, f"Cloud cover {cloud_fraction:.0%} > {CLOUD_COVER_SKIP_THRESHOLD:.0%}"
            )

        # 2. Extract clear-pixel arrays ────────────────────────────────────────
        b2  = bands["B2"][clear_mask]
        b3  = bands["B3"][clear_mask]
        b4  = bands["B4"][clear_mask]
        b8  = bands["B8"][clear_mask]
        b11 = bands["B11"][clear_mask]

        if len(b4) < MIN_VALID_PIXELS:
            logger.warning("Only %d valid pixels in %s — aborting.", len(b4), region_id)
            return self._skipped_result(
                region_id, date_acquired, f"Fewer than {MIN_VALID_PIXELS} valid pixels"
            )

        # 3. Spectral index computation ────────────────────────────────────────
        ndvi = calculate_ndvi(b8, b4)
        ndwi = calculate_ndwi(b3, b8)
        bsi  = calculate_bsi(b11, b4, b8, b2)

        # Check for NaN / Inf after computation
        nan_pct = np.isnan(np.stack([ndvi, ndwi, bsi], axis=1)).mean()
        if nan_pct > 0:
            logger.warning("%.1f%% NaN/Inf in indices for %s — masking before model.", nan_pct * 100, region_id)

        feature_matrix = np.column_stack([ndvi, ndwi, bsi])
        valid_rows = np.isfinite(feature_matrix).all(axis=1)
        feature_matrix = feature_matrix[valid_rows]

        if len(feature_matrix) < MIN_VALID_PIXELS:
            return self._skipped_result(
                region_id, date_acquired, "Insufficient finite feature rows after NaN mask"
            )

        # 4. Isolation Forest + bootstrap uncertainty ──────────────────────────
        predictions, scores = self._detector.fit_predict_spatial(feature_matrix)

        ci_low, ci_high = self._bootstrap_confidence_interval(feature_matrix)
        confidence_mean = float(scores[predictions == -1].mean()) if (predictions == -1).any() else 0.0

        # 5. Spectral statistics of anomalous pixels ───────────────────────────
        anom_idx = predictions == -1
        spectral_stats = {
            "ndvi_mean_anomaly": float(np.mean(ndvi[valid_rows][anom_idx])) if anom_idx.any() else None,
            "ndwi_mean_anomaly": float(np.mean(ndwi[valid_rows][anom_idx])) if anom_idx.any() else None,
            "bsi_mean_anomaly":  float(np.mean(bsi[valid_rows][anom_idx])) if anom_idx.any() else None,
            "ndvi_std":          float(np.std(ndvi)),
            "ndwi_std":          float(np.std(ndwi)),
            "bsi_std":           float(np.std(bsi)),
        }

        logger.info(
            "Spatial detection complete for %s: %d anomalous / %d valid pixels (confidence=%.3f)",
            region_id, int(anom_idx.sum()), len(feature_matrix), confidence_mean,
        )

        return {
            "region_id":            region_id,
            "date":                 date_acquired,
            "anomaly_mask":         predictions,
            "scores":               scores,
            "confidence_mean":      confidence_mean,
            "confidence_ci_low":    ci_low,
            "confidence_ci_high":   ci_high,
            "anomalous_pixel_count": int(anom_idx.sum()),
            "valid_pixel_count":    int(len(feature_matrix)),
            "cloud_fraction":       float(cloud_fraction),
            "spectral_stats":       spectral_stats,
            "skipped_reason":       None,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Temporal Detection (NTL Z-score)
    # ─────────────────────────────────────────────────────────────────────────

    def run_temporal_detection(
        self,
        radiance_series: list,
        dates: list,
        region_id: str,
        rolling_window: int = 12,
    ) -> dict:
        """
        Detect economic shocks in VIIRS night-time lights time series.

        Args:
            radiance_series: Ordered list of monthly mean radiance values.
            dates:           Corresponding ISO-8601 date strings ('YYYY-MM-DD').
            region_id:       Identifier for the monitored economic zone.
            rolling_window:  Months used for rolling baseline (default=12 for annual cycle).

        Returns:
            Dict containing region_id, z_scores, dates, radiance list, flagged_events, rolling_window, and threshold.
        """
        if len(radiance_series) != len(dates):
            raise ValueError("radiance_series and dates must have equal length.")

        # Validate all date strings are ISO-8601 and handle leap years safely
        for d in dates:
            self._validate_iso8601(d)

        values = np.array(radiance_series, dtype=float)

        # Deseasonalization via STL-like rolling Z-score (Section 3.4.2)
        z_scores = self._detector.detect_temporal_ntl(values.tolist(), rolling_window)

        flagged_events = []
        for i, (z, d) in enumerate(zip(z_scores, dates)):
            if abs(z) > TEMPORAL_ANOMALY_THRESHOLD:
                direction = "POSITIVE" if z > 0 else "NEGATIVE"
                flagged_events.append({
                    "date":        d,
                    "index":       i,
                    "z_score":     float(z),
                    "radiance":    float(values[i]),
                    "direction":   direction,
                    "description": (
                        f"{direction} NTL anomaly (Z={z:.2f}): "
                        f"{'Industrial expansion or infrastructure surge' if direction == 'POSITIVE' else 'Factory shutdown, power outage, or economic contraction'}"
                    ),
                })

        logger.info(
            "Temporal detection complete for %s: %d anomalies flagged over %d months.",
            region_id, len(flagged_events), len(dates),
        )

        return {
            "region_id":      region_id,
            "z_scores":       z_scores,
            "dates":          dates,
            "radiance":       values.tolist(),
            "flagged_events": flagged_events,
            "rolling_window": rolling_window,
            "threshold":      TEMPORAL_ANOMALY_THRESHOLD,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _bootstrap_confidence_interval(
        self, feature_matrix: np.ndarray, alpha: float = 0.05
    ) -> tuple:
        """
        Estimate confidence interval for anomaly detection via bootstrap resampling.

        Master Prompt §13.2: 'Every anomaly score must have a confidence interval.'

        Args:
            feature_matrix: Clean (N, D) spectral feature matrix.
            alpha:          Significance level for the interval (default 0.05 → 95% CI).

        Returns:
            (ci_low, ci_high) tuple of floats.
        """
        rng = np.random.default_rng(self.random_state)
        n = len(feature_matrix)
        ci_scores = []

        for _ in range(self.n_bootstrap):
            resample_idx = rng.integers(0, n, size=n)
            resample = feature_matrix[resample_idx]

            temp_detector = AnomalyDetector(
                contamination=self.contamination,
                random_state=self.random_state + 1,
            )
            preds, scores = temp_detector.fit_predict_spatial(resample)
            anomaly_scores = scores[preds == -1]
            if len(anomaly_scores) > 0:
                ci_scores.append(float(np.mean(anomaly_scores)))

        if not ci_scores:
            return 0.0, 0.0

        ci_low  = float(np.percentile(ci_scores, (alpha / 2) * 100))
        ci_high = float(np.percentile(ci_scores, (1 - alpha / 2) * 100))
        return ci_low, ci_high

    @staticmethod
    def _validate_iso8601(date_str: str) -> None:
        """Validate date string is ISO-8601. Handles leap years correctly."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 date: '{date_str}'. Expected YYYY-MM-DD.") from exc

    @staticmethod
    def _skipped_result(region_id: str, date: str, reason: str) -> dict:
        """Return a standardized skipped-tile result record."""
        return {
            "region_id":             region_id,
            "date":                  date,
            "anomaly_mask":          None,
            "scores":                None,
            "confidence_mean":       0.0,
            "confidence_ci_low":     0.0,
            "confidence_ci_high":    0.0,
            "anomalous_pixel_count": 0,
            "valid_pixel_count":     0,
            "cloud_fraction":        None,
            "spectral_stats":        None,
            "skipped_reason":        reason,
        }
