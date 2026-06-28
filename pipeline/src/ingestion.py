"""
ingestion.py — Rate-limited, mock-safe satellite data ingestion layer.

Interfaces with Google Earth Engine (GEE), Copernicus CDSE, and the
World Bank REST API. All methods degrade gracefully to reproducible
mock data generators when credentials are absent.

Rate-limiting strategy:
    - Exponential backoff with jitter (Section 13.4 edge cases)
    - Max 3 retries per request, starting at 1-second delay

Author: Eren Ozturk — CZU Prague PEF KII Bachelor Thesis 2026
"""

import json
import logging
import os
import time
import urllib.request

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False
    logging.warning("earthengine-api not installed. Running in mock-only mode.")

class SatelliteDataIngester:
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT", "tesis-500804")
        self.authenticated = False
        
    def authenticate_gee(self) -> bool:
        """
        Authenticate and initialize Google Earth Engine.
        Falls back to mock mode if credentials are not found.
        """
        if not EE_AVAILABLE:
            logging.info("Earth Engine SDK unavailable. Initializing mock GEE connection.")
            return False
            
        # Check for local client_secret.json to configure custom OAuth client
        client_secret_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "client_secret.json"))
        if os.path.exists(client_secret_path):
            try:
                with open(client_secret_path, "r", encoding="utf-8") as f:
                    secret_data = json.load(f)
                installed_info = secret_data.get("installed", {})
                if installed_info:
                    client_id = installed_info.get("client_id")
                    client_secret_val = installed_info.get("client_secret")
                    project_id_val = installed_info.get("project_id")
                    if client_id and client_secret_val:
                        logging.info("Detected local client_secret.json. Configuring Earth Engine custom client credentials.")
                        ee.oauth.CLIENT_ID = client_id
                        ee.oauth.CLIENT_SECRET = client_secret_val
                    if project_id_val and (not os.getenv("GCP_PROJECT") or self.project_id == "tesis-500804"):
                        logging.info(f"Using project ID from client_secret: {project_id_val}")
                        self.project_id = project_id_val
            except Exception as e:
                logging.warning(f"Failed to load client_secret.json for custom client configuration: {e}")

        try:
            # Check if already authenticated or can load default credentials
            logging.info(f"Attempting to initialize GEE with project: {self.project_id}")
            ee.Initialize(project=self.project_id)
            self.authenticated = True
            logging.info("GEE successfully initialized.")
            return True
        except Exception as e:
            logging.warning(f"GEE authentication failed: {e}. Fallback to mock dataset generator is enabled.")
            self.authenticated = False
            return False

    def fetch_sentinel2_data(self, bbox: list, start_date: str, end_date: str) -> dict:
        """
        Query Sentinel-2 MSI collection within a bounding box and date range.
        
        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            
        Returns:
            Dict containing bands metadata or mock raster arrays.
        """
        if not self.authenticated:
            logging.info(f"Mocking Sentinel-2 fetch for bbox {bbox} from {start_date} to {end_date}")
            # Generate synthetic 100x100 raster grids
            size = (100, 100)
            np.random.seed(42)
            return {
                "source": "Mock Sentinel-2 (Top of Atmosphere)",
                "B2": np.random.uniform(0.01, 0.15, size), # Blue
                "B3": np.random.uniform(0.02, 0.18, size), # Green
                "B4": np.random.uniform(0.01, 0.12, size), # Red
                "B8": np.random.uniform(0.20, 0.65, size), # NIR
                "B11": np.random.uniform(0.05, 0.45, size), # SWIR1
                "QA60": np.zeros(size, dtype=int)         # Quality band (0 = clear)
            }
            
        # GEE real query logic
        try:
            geometry = ee.Geometry.BBox(*bbox)
            collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(geometry)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
                .sort("CLOUDY_PIXEL_PERCENTAGE")
            )
            
            image = collection.first()
            if image is None:
                raise ValueError("No Sentinel-2 imagery matches filters.")
                
            logging.info("Real Sentinel-2 image metadata retrieved from GEE.")
            return {"image_object": image, "source": "GEE Sentinel-2 SR"}
        except Exception as e:
            logging.error(f"Failed to fetch real GEE image: {e}. Fallback to mock.")
            self.authenticated = False
            return self.fetch_sentinel2_data(bbox, start_date, end_date)

    def fetch_viirs_ntl(self, bbox: list, start_date: str, end_date: str) -> dict:
        """
        Query monthly VIIRS DNB night-time lights average radiance.
        """
        if not self.authenticated:
            logging.info("Mocking VIIRS NTL time series.")
            months = 36
            np.random.seed(42)
            # Create a mock economic shock baseline (sudden drop at month 18)
            radiance_values = np.random.normal(15.0, 1.2, months)
            radiance_values[18:22] -= 4.5  # Simulate industrial shutdown anomaly
            dates = [f"2023-{(i%12)+1:02d}-01" for i in range(months)]
            return {
                "source": "Mock VIIRS Monthly Composites",
                "dates": dates,
                "radiance": radiance_values.tolist()
            }
            
        try:
            geometry = ee.Geometry.BBox(*bbox)
            collection = (
                ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
                .filterBounds(geometry)
                .filterDate(start_date, end_date)
            )
            # Spatial mean reducer calculation would go here
            logging.info("Real VIIRS DNB night-time lights queried.")
            return {"collection": collection, "source": "GEE VIIRS Monthly"}
        except Exception as e:
            logging.error(f"Failed to fetch real VIIRS DNB: {e}. Fallback to mock.")
            self.authenticated = False
            return self.fetch_viirs_ntl(bbox, start_date, end_date)

    def fetch_landsat_data(self, bbox: list, start_date: str, end_date: str) -> dict:
        """
        Query Landsat-8/9 OLI Tier-1 Surface Reflectance collection.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'

        Returns:
            Dict with bands B2-B7 as NumPy arrays, or mock arrays in offline mode.
        """
        if not self.authenticated:
            logging.info("Mocking Landsat-8/9 OLI fetch for bbox %s.", bbox)
            size = (100, 100)
            rng = np.random.default_rng(42)
            return {
                "source": "Mock Landsat-8/9 OLI Surface Reflectance",
                "B2":  rng.uniform(0.01, 0.14, size),   # Blue
                "B3":  rng.uniform(0.02, 0.18, size),   # Green
                "B4":  rng.uniform(0.01, 0.12, size),   # Red
                "B5":  rng.uniform(0.18, 0.60, size),   # NIR
                "B6":  rng.uniform(0.05, 0.40, size),   # SWIR1
                "B7":  rng.uniform(0.03, 0.25, size),   # SWIR2
                "QA_PIXEL": np.zeros(size, dtype=int),  # Quality band
            }

        try:
            geometry = ee.Geometry.BBox(*bbox)
            # Merge Landsat-8 and Landsat-9 collections for continuous 8-day coverage
            l8 = (
                ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                .filterBounds(geometry)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUD_COVER", 20))
            )
            l9 = (
                ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                .filterBounds(geometry)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUD_COVER", 20))
            )
            merged = l8.merge(l9).sort("CLOUD_COVER")
            image = merged.first()
            if image is None:
                raise ValueError("No Landsat imagery matches filters.")
            logging.info("Real Landsat-8/9 image retrieved from GEE.")
            return {"image_object": image, "source": "GEE Landsat-8/9 SR"}
        except Exception as e:
            logging.error("Failed to fetch Landsat from GEE: %s. Falling back to mock.", e)
            self.authenticated = False
            return self.fetch_landsat_data(bbox, start_date, end_date)

    def fetch_worldbank_gdp(
        self,
        country_code: str,
        start_year: int,
        end_year: int,
        max_retries: int = 3,
    ) -> list:
        """
        Fetch annual GDP growth rate (%) from the World Bank Open Data API.

        Uses exponential backoff with jitter for rate-limit resilience
        (Master Prompt §13.4 edge case: 'API rate limit exceeded').

        Args:
            country_code: ISO-3 Alpha code (e.g., 'CZE', 'CHL', 'PER').
            start_year:   First year of requested series.
            end_year:     Last year of requested series.
            max_retries:  Number of retry attempts on transient failures.

        Returns:
            List of dicts: [{'year': int, 'gdp_growth_pct': float}]
        """
        indicator = "NY.GDP.MKTP.KD.ZG"
        url = (
            f"https://api.worldbank.org/v2/country/{country_code}"
            f"/indicator/{indicator}?format=json"
            f"&date={start_year}:{end_year}&mrv=100"
        )

        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    raw = json.loads(resp.read().decode())
                records = raw[1] if (isinstance(raw, list) and len(raw) > 1) else []
                result = [
                    {"year": int(r["date"]), "gdp_growth_pct": float(r["value"])}
                    for r in records if r.get("value") is not None
                ]
                result.sort(key=lambda x: x["year"])
                logging.info(
                    "World Bank: fetched %d GDP records for %s (%d-%d).",
                    len(result), country_code, start_year, end_year,
                )
                return result
            except Exception as exc:
                wait = (2 ** attempt) + np.random.uniform(0, 0.5)
                logging.warning(
                    "World Bank API attempt %d/%d failed: %s. Retrying in %.1fs.",
                    attempt + 1, max_retries, exc, wait,
                )
                if attempt < max_retries - 1:
                    time.sleep(wait)

        # Fallback mock data for offline mode
        logging.warning("World Bank API unreachable after %d retries. Using mock data.", max_retries)
        mock_rates = {
            "CZE": {2021: -2.4, 2022: 2.5, 2023: -0.4, 2024: 1.3, 2025: 2.8},
            "CHL": {2021: 11.7, 2022: 2.4, 2023: 0.2,  2024: 2.6, 2025: 2.9},
            "PER": {2021: 13.5, 2022: 2.7, 2023: -0.6, 2024: 3.0, 2025: 3.3},
        }
        country_data = mock_rates.get(country_code, {})
        return [
            {"year": y, "gdp_growth_pct": v}
            for y, v in country_data.items()
            if start_year <= y <= end_year
        ]
