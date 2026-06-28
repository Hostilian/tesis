import numpy as np
from datetime import datetime


def calculate_ndvi(nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
    """
    Calculate the Normalized Difference Vegetation Index (NDVI).
    NDVI = (NIR - Red) / (NIR + Red)

    Args:
        nir_band: Numpy array representing Near-Infrared band reflectance.
        red_band: Numpy array representing Red band reflectance.

    Returns:
        Numpy array with NDVI values in range [-1.0, 1.0].
    """
    denominator = nir_band + red_band
    # Avoid division by zero
    denominator[denominator == 0.0] = 1e-5
    ndvi = (nir_band - red_band) / denominator
    return np.clip(ndvi, -1.0, 1.0)


def calculate_ndwi(green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """
    Calculate the Normalized Difference Water Index (NDWI) for surface water monitoring.
    NDWI = (Green - NIR) / (Green + NIR)

    Args:
        green_band: Numpy array representing Green band reflectance.
        nir_band: Numpy array representing Near-Infrared band reflectance.

    Returns:
        Numpy array with NDWI values in range [-1.0, 1.0].
    """
    denominator = green_band + nir_band
    denominator[denominator == 0.0] = 1e-5
    ndwi = (green_band - nir_band) / denominator
    return np.clip(ndwi, -1.0, 1.0)


def calculate_bsi(
    swir1_band: np.ndarray,
    red_band: np.ndarray,
    nir_band: np.ndarray,
    blue_band: np.ndarray
) -> np.ndarray:
    """
    Calculate the Bare Soil Index (BSI) for exposed soil and mining footprint extraction.
    BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))

    Args:
        swir1_band: Shortwave-Infrared band.
        red_band: Red band.
        nir_band: Near-Infrared band.
        blue_band: Blue band.

    Returns:
        Numpy array with BSI values in range [-1.0, 1.0].
    """
    numerator = (swir1_band + red_band) - (nir_band + blue_band)
    denominator = (swir1_band + red_band) + (nir_band + blue_band)
    denominator[denominator == 0.0] = 1e-5
    bsi = numerator / denominator
    return np.clip(bsi, -1.0, 1.0)


def apply_sentinel_cloud_mask(qa_band: np.ndarray) -> np.ndarray:
    """
    Generates a boolean mask for clouds and cirrus in Sentinel-2 QA60 band.
    Sentinel-2 QA60 bit 10 is opaque clouds, bit 11 is cirrus clouds.

    Args:
        qa_band: Integer array of the QA60 band.

    Returns:
        Boolean array where True indicates clear pixels and False indicates clouds.
    """
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    # Identify cloudy pixels
    is_cloud = (qa_band & cloud_bit_mask) != 0
    is_cirrus = (qa_band & cirrus_bit_mask) != 0

    # Return clear pixels mask (True for clear, False for clouds)
    return ~(is_cloud | is_cirrus)


def calculate_temporal_zscores(values: np.ndarray, rolling_window: int = 12) -> np.ndarray:
    """
    Calculate the temporal Z-score anomalies on a 1D time series.
    Z = (value - rolling_mean) / rolling_std

    Args:
        values: 1D array of time series data.
        rolling_window: Window size for calculating historical mean/std.

    Returns:
        Numpy array of Z-scores. First rolling_window entries will be 0.0.
    """
    n = len(values)
    z_scores = np.zeros(n)
    for i in range(n):
        if i < rolling_window:
            z_scores[i] = 0.0
            continue
        history = values[max(0, i - rolling_window):i]
        mean = np.mean(history)
        std = np.std(history)
        if std == 0.0:
            std = 1e-5
        z_scores[i] = (values[i] - mean) / std
    return z_scores


def validate_bbox(bbox: list[float]) -> None:
    """Raise ValueError if bbox is not [lon_min, lat_min, lon_max, lat_max]."""
    if len(bbox) != 4:
        raise ValueError("bbox must contain exactly four coordinates")

    lon_min, lat_min, lon_max, lat_max = bbox

    if not (-180 <= lon_min < lon_max <= 180):
        raise ValueError(f"Invalid longitude range: {lon_min}, {lon_max}")
    if not (-90 <= lat_min < lat_max <= 90):
        raise ValueError(f"Invalid latitude range: {lat_min}, {lat_max}")


def validate_date_iso8601(date_str: str) -> None:
    """Validate ISO-8601 date string with leap-year awareness."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid ISO-8601 date: {date_str!r}") from exc
