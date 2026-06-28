import os
import json
import logging

class GeospatialExporter:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../docs/data")
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
    def export_anomalies_json(self, anomalies: list, filename: str = "anomalies.json") -> str:
        """
        Serialize list of anomaly dictionaries into a single JSON dataset.
        """
        filepath = os.path.join(self.output_dir, filename)
        logging.info(f"Saving serialized anomalies to {filepath}...")
        
        try:
            with open(filepath, "w") as f:
                json.dump(anomalies, f, indent=2)
            logging.info("Anomalies JSON successfully written.")
            return filepath
        except Exception as e:
            logging.error(f"Failed to write anomalies JSON: {e}")
            raise e

    def export_geojson_regions(self, regions: list, filename: str = "regions.geojson") -> str:
        """
        Convert bounding box limits into a standard GeoJSON FeatureCollection for map rendering.
        """
        features = []
        for reg in regions:
            name = reg["name"]
            bbox = reg["bbox"] # [min_lon, min_lat, max_lon, max_lat]
            
            # Construct polygon coordinates: counter-clockwise loop
            coords = [[
                [bbox[0], bbox[1]],
                [bbox[2], bbox[1]],
                [bbox[2], bbox[3]],
                [bbox[0], bbox[3]],
                [bbox[0], bbox[1]]
            ]]
            
            features.append({
                "type": "Feature",
                "properties": {
                    "name": name,
                    "type": reg.get("type", "study_area"),
                    "description": reg.get("description", "")
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coords
                }
            })
            
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }
        
        filepath = os.path.join(self.output_dir, filename)
        logging.info(f"Saving GeoJSON boundaries to {filepath}...")
        try:
            with open(filepath, "w") as f:
                json.dump(geojson_data, f, indent=2)
            logging.info("GeoJSON boundaries successfully written.")
            return filepath
        except Exception as e:
            logging.error(f"Failed to write GeoJSON: {e}")
            raise e

    def export_api_endpoints(self, anomalies: list, datasets_meta: list = None) -> None:
        """
        Generate static REST API endpoints mirroring a real API in docs/api/v1/
        """
        import shutil
        api_dir = os.path.abspath(os.path.join(self.output_dir, "../api/v1"))
        os.makedirs(api_dir, exist_ok=True)
        
        # 1. anomalies endpoint
        anoms_dir = os.path.join(api_dir, "anomalies")
        os.makedirs(anoms_dir, exist_ok=True)
        
        # Write list at /api/v1/anomalies/index.json
        list_path = os.path.join(anoms_dir, "index.json")
        logging.info(f"Saving static API endpoint: {list_path}")
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(anomalies, f, indent=2)
            
        # Write individual anomaly details at /api/v1/anomalies/<id>/index.json
        for anom in anomalies:
            anom_id = anom["id"]
            single_anom_dir = os.path.join(anoms_dir, anom_id)
            os.makedirs(single_anom_dir, exist_ok=True)
            single_path = os.path.join(single_anom_dir, "index.json")
            logging.info(f"Saving static API endpoint: {single_path}")
            with open(single_path, "w", encoding="utf-8") as f:
                json.dump(anom, f, indent=2)
                
        # 2. datasets endpoint
        if datasets_meta is None:
            datasets_meta = [
                {
                    "name": "Sentinel-2 MSI",
                    "resolution": "10m - 20m",
                    "revisit": "5 days",
                    "description": "Multi-spectral optical data containing visible, RedEdge, NIR, and SWIR bands."
                },
                {
                    "name": "Sentinel-1 SAR",
                    "resolution": "10m",
                    "revisit": "6 - 12 days",
                    "description": "Synthetic Aperture Radar backscatter (VV and VH polarizations) penetrating cloud cover."
                },
                {
                    "name": "Suomi-NPP VIIRS DNB",
                    "resolution": "500m",
                    "revisit": "Daily / Monthly Composites",
                    "description": "Day/Night Band sensor capturing low-light night-time emissions, GDP proxy."
                }
            ]
        datasets_dir = os.path.join(api_dir, "datasets")
        os.makedirs(datasets_dir, exist_ok=True)
        datasets_path = os.path.join(datasets_dir, "index.json")
        logging.info(f"Saving static API endpoint: {datasets_path}")
        with open(datasets_path, "w", encoding="utf-8") as f:
            json.dump(datasets_meta, f, indent=2)
            
        # 3. status endpoint
        import datetime
        status_data = {
            "status": "online",
            "last_pipeline_run": datetime.datetime.utcnow().isoformat() + "Z",
            "anomalies_count": len(anomalies),
            "environment": "GitHub Actions CI/CD" if os.getenv("GITHUB_ACTIONS") else "development"
        }
        status_dir = os.path.join(api_dir, "status")
        os.makedirs(status_dir, exist_ok=True)
        status_path = os.path.join(status_dir, "index.json")
        logging.info(f"Saving static API endpoint: {status_path}")
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2)
