# Appendix C: Dataset Metadata

This appendix lists the sensor specifications, band wavelengths, and spatial resolutions of the primary satellite datasets utilized in this thesis.

## C.1 Sentinel-2 MSI Spectral Bands
The Multi-Spectral Instrument (MSI) aboard Sentinel-2 provides 13 spectral bands at varying resolutions:

| Band Number | Band Name | Central Wavelength (nm) | Spatial Resolution (m) | Use in Pipeline |
|---|---|---|---|---|
| **B02** | Blue | 490 | 10 | Bare Soil Index (BSI) calculation |
| **B03** | Green | 560 | 10 | NDWI calculation |
| **B04** | Red | 665 | 10 | NDVI and BSI calculation |
| **B08** | NIR (Near-Infrared) | 842 | 10 | NDVI, NDWI, and BSI calculation |
| **B11** | SWIR 1 (Shortwave-Infrared) | 1610 | 20 | BSI calculation |
| **QA60** | Quality Assessment | N/A | 60 | Cloud and cirrus bitmasking |

## C.2 Landsat-8/9 OLI Spectral Bands
The Operational Land Imager (OLI) on Landsat 8/9 aligns closely with Sentinel-2 bands:

| Band Number | Band Name | Central Wavelength (nm) | Spatial Resolution (m) | Use in Pipeline |
|---|---|---|---|---|
| **B2** | Blue | 482 | 30 | Bare Soil Index (BSI) |
| **B3** | Green | 561 | 30 | NDWI water index |
| **B4** | Red | 655 | 30 | NDVI and BSI |
| **B5** | NIR | 865 | 30 | NDVI, NDWI, and BSI |
| **B6** | SWIR 1 | 1609 | 30 | BSI bare soil indicator |
| **QA_PIXEL** | Pixel Quality | N/A | 30 | Cloud and shadow masking |

## C.3 Suomi-NPP VIIRS Day/Night Band (DNB)
*   **Sensor Type**: Visible Infrared Imaging Radiometer Suite (VIIRS).
*   **Spatial Resolution**: 15 arc-seconds (approximately 500 meters at the equator).
*   **Spectral Range**: 500–900 nm (panchromatic visible/near-infrared band sensitive to low-light).
*   **Radiometric Calibration**: Absolute radiance in units of $\text{nW}\cdot\text{cm}^{-2}\cdot\text{sr}^{-1}$.
