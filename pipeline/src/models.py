import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from pipeline.src.utils import calculate_temporal_zscores

class AnomalyDetector:
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.spatial_model = None
        
    def fit_predict_spatial(self, features: np.ndarray) -> tuple:
        """
        Train Isolation Forest on spatial spectral features and predict outlier masks.
        
        Args:
            features: 2D array of shape (N_pixels, D_features)
            
        Returns:
            predictions: Array of predictions (1 = normal, -1 = anomaly)
            scores: Normalized anomaly scores in range [0, 1]
        """
        logging.info(f"Fitting Isolation Forest on {features.shape[0]} pixel samples...")
        self.spatial_model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )
        
        # Fit and predict
        predictions = self.spatial_model.fit_predict(features)
        
        # Get raw decision function scores (lower values mean more anomalous)
        raw_scores = self.spatial_model.decision_function(features)
        
        # Normalize scores to [0, 1] range (where 1 indicates high anomaly probability)
        # Shift so that lower raw scores mapped to higher normalized scores
        min_raw, max_raw = raw_scores.min(), raw_scores.max()
        if max_raw == min_raw:
            scores = np.zeros_like(raw_scores)
        else:
            scores = 1.0 - ((raw_scores - min_raw) / (max_raw - min_raw))
            
        logging.info("Isolation Forest fitting and scoring complete.")
        return predictions, scores

    def detect_temporal_ntl(self, radiance_series: list, rolling_window: int = 12) -> list:
        """
        Detect temporal anomalies in night-time lights using rolling Z-scores.
        
        Args:
            radiance_series: List or array of monthly light radiance.
            rolling_window: Window size for base calculation.
            
        Returns:
            List of Z-scores corresponding to each month.
        """
        logging.info(f"Computing rolling Z-scores for NTL series with window size {rolling_window}...")
        values = np.array(radiance_series)
        z_scores = calculate_temporal_zscores(values, rolling_window)
        return z_scores.tolist()
