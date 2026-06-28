import logging
import numpy as np
from pipeline.src.utils import calculate_ndvi, calculate_ndwi, calculate_bsi, apply_sentinel_cloud_mask

class GeospatialPreprocessor:
    def __init__(self):
        pass
        
    def process_raw_bands(self, band_dict: dict) -> dict:
        """
        Takes raw multi-spectral bands, applies cloud masks, 
        and calculates NDVI, NDWI, and BSI.
        
        Args:
            band_dict: Dictionary containing band arrays (B2, B3, B4, B8, B11, QA60)
            
        Returns:
            Dictionary containing processed indices and masks.
        """
        logging.info("Preprocessing raw multi-spectral bands...")
        
        # Load bands
        blue = band_dict["B2"]
        green = band_dict["B3"]
        red = band_dict["B4"]
        nir = band_dict["B8"]
        swir1 = band_dict["B11"]
        qa = band_dict["QA60"]
        
        # Apply cloud masking
        clear_mask = apply_sentinel_cloud_mask(qa)
        
        # Calculate indices
        ndvi = calculate_ndvi(nir, red)
        ndwi = calculate_ndwi(green, nir)
        bsi = calculate_bsi(swir1, red, nir, blue)
        
        # Apply cloud mask to indices (mask out clouds to NaN)
        ndvi_masked = np.where(clear_mask, ndvi, np.nan)
        ndwi_masked = np.where(clear_mask, ndwi, np.nan)
        bsi_masked = np.where(clear_mask, bsi, np.nan)
        
        logging.info("Spectral indices computed successfully.")
        return {
            "ndvi": ndvi_masked,
            "ndwi": ndwi_masked,
            "bsi": bsi_masked,
            "clear_mask": clear_mask
        }

    def prepare_ml_features(self, processed_dict: dict) -> tuple:
        """
        Flattens multi-spectral bands and indices, filtering out NaN values,
        to create a 2D feature matrix (N_pixels, D_features) for training ML models.
        
        Returns:
            features: 2D numpy array of valid pixels.
            coordinates: Tuple of (row_idx, col_idx) matching each feature index.
        """
        ndvi = processed_dict["ndvi"]
        ndwi = processed_dict["ndwi"]
        bsi = processed_dict["bsi"]
        
        rows, cols = ndvi.shape
        row_grid, col_grid = np.meshgrid(range(rows), range(cols), indexing="ij")
        
        # Flatten all
        ndvi_flat = ndvi.flatten()
        ndwi_flat = ndwi.flatten()
        bsi_flat = bsi.flatten()
        row_flat = row_grid.flatten()
        col_flat = col_grid.flatten()
        
        # Filter where all indices are valid
        valid_indices = ~np.isnan(ndvi_flat) & ~np.isnan(ndwi_flat) & ~np.isnan(bsi_flat)
        
        features = np.column_stack((
            ndvi_flat[valid_indices],
            ndwi_flat[valid_indices],
            bsi_flat[valid_indices]
        ))
        
        coordinates = (row_flat[valid_indices], col_flat[valid_indices])
        logging.info(f"Prepared feature matrix with {features.shape[0]} valid pixels.")
        return features, coordinates
