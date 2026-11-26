"""Recompute the Alentejo difference with product-specific BOA calibration."""
import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree

import matplotlib.pyplot as plt
import numpy as np
import requests
from planetary_computer import sign_inplace
from pystac_client import Client

import soil_surface_pair_public_preview as pilot


def calibrate(scene):
    bands = pilot.read_real_bands(scene)
    response = requests.get(scene.assets["product-metadata"].href, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Product metadata unavailable ({response.status_code})")
    root = ElementTree.fromstring(response.content)
    scale = float(root.findtext(".//BOA_QUANTIFICATION_VALUE"))
    offsets = {int(x.attrib["band_id"]): float(x.text)
               for x in root.findall(".//BOA_ADD_OFFSET")}
    valid = np.isin(bands["SCL"], [4, 5])
    for key, number in [("B04", 3), ("B08", 7)]:
        raw = bands[key]
        valid &= np.isfinite(raw) & (raw > 0) & (raw < 65535)
        bands[key] = (raw + offsets[number]) / scale
        valid &= bands[key] >= 0
    red, nir = bands["B04"], bands["B08"]
    valid &= nir + red > 0
    ndvi = np.divide(nir-red, nir+red, out=np.full_like(red, np.nan), where=valid)
    return ndvi, {"item": scene.id, "utc": scene.properties["datetime"],
                  "processing_baseline": scene.properties["s2:processing_baseline"],
                  "metadata_sha256": hashlib.sha256(response.content).hexdigest(),
                  "quantification": scale, "red_offset": offsets[3], "nir_offset": offsets[7],
                  "valid_cells": int(valid.sum())}


def main():
    start = time.monotonic()
    repo = Path(__file__).resolve().parents[2]
    archive = json.loads((repo / "docs/data/observed_alentejo_soil5_pair_20261123.json").read_text())
    catalog = Client.open(pilot.PUBLIC_STAC_URL, modifier=sign_inplace)
    collection = catalog.get_collection(pilot.COLLECTION)
    observations = []
    for period, recorded in zip(pilot.DATERANGES, archive["scenes"]):
        scene = pilot.best_public_scene(catalog, period)
        if scene.id != recorded["scene_id"]:
            raise RuntimeError("Catalogue selection differs from archived scene")
        observations.append(calibrate(scene))
    delta = observations[1][0] - observations[0][0]
    valid = np.isfinite(delta)
    if valid.mean() < 0.5:
        raise ValueError("Less than half the common grid is usable")
    out = repo / "docs/data"
    fig, ax = plt.subplots(figsize=(6, 5))
    limit = np.nanmax(np.abs(delta))
    im = ax.imshow(delta, cmap="BrBG", vmin=-limit, vmax=limit, interpolation="nearest")
    fig.colorbar(im, ax=ax, label="NDVI difference (later minus earlier)")
    ax.set(title="Alentejo | 12 July 2024 to 27 June 2025", xlabel="Grid column (east →)", ylabel="Grid row (south →)")
    fig.tight_layout()
    fig.savefig(out / "alentejo-change.png", dpi=150)
    plt.close(fig)
    result = {"category": "observation-derived result", "interpretation": "unverified interpretation",
              "command": "python research/prototypes/alentejo_change.py",
              "source": pilot.PUBLIC_STAC_URL, "collection": pilot.COLLECTION, "license": collection.license,
              "code_base": subprocess.check_output(["git","rev-parse","HEAD"], cwd=repo,text=True).strip(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scenes": [x[1] for x in observations], "bbox": pilot.BBOX, "crs":"EPSG:4326",
              "shape": delta.shape, "valid_overlap": int(valid.sum()), "median_delta": float(np.nanmedian(delta)),
              "absolute_delta_strictly_over": {str(t): int((np.abs(delta)>t).sum()) for t in [0.05,0.10,0.15,0.20]},
              "delta_float32_sha256":hashlib.sha256(delta.astype("<f4").tobytes()).hexdigest(),
              "mask":"Both dates SCL vegetation or bare ground, valid DN and nonnegative calibrated bands",
              "reference_labels":0,"execution":"live catalog, product XML and raster windows",
              "figure":"alentejo-change.png","finished_utc":datetime.now(timezone.utc).isoformat(),
              "seconds":round(time.monotonic()-start,2),"python":platform.python_version(),
              "packages":{p:version(p) for p in ["rasterio","numpy","planetary-computer","pystac-client","matplotlib","requests"]}}
    (out/"alentejo-change.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__ == "__main__":
    main()
