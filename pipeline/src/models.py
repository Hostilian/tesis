from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from pipeline.src.utils import calculate_temporal_zscores

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency path
    import torch
    from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation

    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency path
    torch = None  # type: ignore[assignment]
    AutoImageProcessor = None  # type: ignore[assignment]
    AutoModelForSemanticSegmentation = None  # type: ignore[assignment]
    TORCH_AVAILABLE = False


class AnomalyDetector:
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.spatial_model: IsolationForest | None = None

    def fit_predict_spatial(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Train Isolation Forest on spatial spectral features and predict outlier masks.

        Args:
            features: 2D array of shape (N_pixels, D_features)

        Returns:
            predictions: Array of predictions (1 = normal, -1 = anomaly)
            scores: Normalized anomaly scores in range [0, 1]
        """
        logger.info("Fitting Isolation Forest on %d pixel samples...", features.shape[0])
        self.spatial_model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
        )

        predictions = self.spatial_model.fit_predict(features)
        raw_scores = self.spatial_model.decision_function(features)

        min_raw, max_raw = raw_scores.min(), raw_scores.max()
        if max_raw == min_raw:
            scores = np.zeros_like(raw_scores)
        else:
            scores = 1.0 - ((raw_scores - min_raw) / (max_raw - min_raw))

        logger.info("Isolation Forest fitting and scoring complete.")
        return predictions, scores

    def detect_temporal_ntl(self, radiance_series: list[float], rolling_window: int = 12) -> list[float]:
        """
        Detect temporal anomalies in night-time lights using rolling Z-scores.

        Args:
            radiance_series: List or array of monthly light radiance.
            rolling_window: Window size for base calculation.

        Returns:
            List of Z-scores corresponding to each month.
        """
        logger.info("Computing rolling Z-scores for NTL series with window size %d...", rolling_window)
        values = np.array(radiance_series)
        z_scores = calculate_temporal_zscores(values, rolling_window)
        return z_scores.tolist()


@dataclass(slots=True)
class PrithviInferenceResult:
    vegetation_probability: np.ndarray
    bare_soil_probability: np.ndarray
    water_probability: np.ndarray
    mining_probability: np.ndarray


class PrithviInferenceClient:
    """Optional Prithvi wrapper with deterministic fallback when torch is unavailable."""

    def __init__(self, model_name: str = "ibm-nasa-geospatial/Prithvi-100M") -> None:
        self.model_name = model_name
        self.available = False
        self.device = "cpu"
        self.processor = None
        self.model = None

        if not TORCH_AVAILABLE:
            logger.warning("Prithvi dependencies unavailable; using deterministic fallback only.")
            return

        if torch is not None and torch.cuda.is_available():
            self.device = "cuda"
        elif torch is not None and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            logger.warning("No GPU or MPS accelerator detected; using deterministic fallback only.")
            return

        try:
            self.processor = AutoImageProcessor.from_pretrained(model_name)
            self.model = AutoModelForSemanticSegmentation.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            self.available = True
            logger.info("Prithvi model initialized on %s.", self.device)
        except Exception as exc:  # pragma: no cover - remote model load path
            logger.warning("Failed to initialize Prithvi model: %s", exc)
            self.available = False

    def predict(self, sentinel2_cube: np.ndarray) -> PrithviInferenceResult:
        """
        Return per-class probability maps for a 6-channel Sentinel-2 cube.

        If the model is unavailable, returns deterministic zero-centered fallback maps.
        """
        if sentinel2_cube.ndim != 3 or sentinel2_cube.shape[-1] != 6:
            raise ValueError("sentinel2_cube must have shape (height, width, 6)")

        height, width, _ = sentinel2_cube.shape
        if not self.available or self.processor is None or self.model is None or torch is None:
            zeros = np.zeros((height, width), dtype=np.float32)
            return PrithviInferenceResult(zeros, zeros, zeros, zeros)

        try:
            input_tensor = torch.from_numpy(sentinel2_cube.astype(np.float32)).permute(2, 0, 1).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.model(pixel_values=input_tensor)
                logits = outputs.logits.squeeze(0)
                probabilities = torch.softmax(logits, dim=0).detach().cpu().numpy()

            if probabilities.shape[0] < 4:
                raise ValueError("Prithvi output did not contain four class channels")

            vegetation_probability = probabilities[0]
            bare_soil_probability = probabilities[1]
            water_probability = probabilities[2]
            mining_probability = probabilities[3]
            return PrithviInferenceResult(
                vegetation_probability=vegetation_probability,
                bare_soil_probability=bare_soil_probability,
                water_probability=water_probability,
                mining_probability=mining_probability,
            )
        except Exception as exc:  # pragma: no cover - inference fallback path
            logger.warning("Prithvi inference fallback triggered: %s", exc)
            zeros = np.zeros((height, width), dtype=np.float32)
            return PrithviInferenceResult(zeros, zeros, zeros, zeros)

    @staticmethod
    def ensemble_score(isoforest_score: np.ndarray, mining_probability: np.ndarray) -> np.ndarray:
        """Blend anomaly score and mining probability into a single ensemble score."""
        if isoforest_score.shape != mining_probability.shape:
            raise ValueError("isoforest_score and mining_probability must have the same shape")
        return np.clip(0.6 * isoforest_score + 0.4 * mining_probability, 0.0, 1.0)
