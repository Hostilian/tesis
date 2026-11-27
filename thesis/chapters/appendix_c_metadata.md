# Appendix C: Dataset Metadata

<!-- AI-assisted factual update 2026-11-27: pending supervisor permission -->

This appendix lists the satellite scenes, bands and reference maps used in the case study. Every row is copied by script from the published files named in the "Source" column, under `docs/case-study/data/`. One row (C.2, item 8) was completed with a single metadata request to the Earth Search STAC API on 27 November 2026.

## C.1 Sentinel-2 L2A bands read by the pipeline

| Asset key (Earth Search) | Band | Pixel size (m) | Use in the case study |
|---|---|---|---|
| `blue` | B02 | 10 | BSI (Neves-Corvo); true-colour figures |
| `green` | B03 | 10 | True-colour figures only |
| `red` | B04 | 10 | NDVI and BSI |
| `nir` | B08 | 10 | NDVI and BSI |
| `swir16` | B11 | 20 | BSI; resampled to 10 m (nearest neighbour) |
| `scl` | SCL | 20 | Pixel mask: classes 4, 5 and 6 kept; resampled to 10 m (nearest neighbour) |

Source: `inputs[].assets` (`gsd_m`) and `processing.mask` in `<case>/manifest.json`. Reflectance = DN × scale + offset; scale 0.0001, offset 0 for all items used (`assets.<band>.scale`, `assets.<band>.offset`). The STAC metadata lists an offset of −0.1 (`offset_in_stac_metadata`), but the pixels already have it removed (`earthsearch_boa_offset_applied: true`).

## C.2 Sentinel-2 items in the main runs and the study-area screen

All items are in the Earth Search collection `sentinel-2-l2a`, relative orbit 037, coordinate reference system EPSG:32629 (WGS 84 / UTM zone 29N). `eo:cloud_cover` is the scene cloud share in per cent, as published in STAC.

| # | STAC item id | Study area | Role | Date and time (UTC) | MGRS tile | Processing baseline | eo:cloud_cover (%) | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | `S2A_29SNC_20180818_1_L2A` | Alqueva | before; also study-area screen | 2018-08-18 11:30:42 | 29SNC | 05.00 | 0.007409 | `alqueva_olive/manifest.json` `inputs[]` |
| 2 | `S2C_29SNC_20250821_0_L2A` | Alqueva | after; control after | 2025-08-21 11:31:03 | 29SNC | 05.11 | 0.006082 | `alqueva_olive/manifest.json` `inputs[]` |
| 3 | `S2C_29SNC_20250801_0_L2A` | Alqueva | control before | 2025-08-01 11:31:04 | 29SNC | 05.11 | 0.006858 | `alqueva_olive/manifest.json` `inputs[]` |
| 4 | `S2C_29SNC_20250523_0_L2A` | Alqueva | seasonal (May) date | 2025-05-23 11:31:02 | 29SNC | 05.11 | 0.011772 | `alqueva_olive/manifest.json` `inputs[]` |
| 5 | `S2A_29SNB_20180818_1_L2A` | Neves-Corvo | before | 2018-08-18 11:30:57 | 29SNB | 05.00 | 0.013464 | `neves_corvo_mine/manifest.json` `inputs[]` |
| 6 | `S2C_29SNB_20250821_0_L2A` | Neves-Corvo | after; control after | 2025-08-21 11:31:17 | 29SNB | 05.11 | 0.006301 | `neves_corvo_mine/manifest.json` `inputs[]` |
| 7 | `S2C_29SNB_20250801_0_L2A` | Neves-Corvo | control before | 2025-08-01 11:31:19 | 29SNB | 05.11 | 0.015033 | `neves_corvo_mine/manifest.json` `inputs[]` |
| 8 | `S2B_29SNC_20240821_0_L2A` | Tile 29SNC | study-area screen only | 2024-08-21 11:30:43 | 29SNC | 05.11 | 0.008451 | `screening_29SNC.json` `items[]`; metadata from the STAC item |

## C.3 Sentinel-2 items in the second date pair (check on other dates)

| STAC item id | Study area | Role | Date and time (UTC) | Processing baseline | eo:cloud_cover (%) |
|---|---|---|---|---|---|
| `S2B_29SNC_20180823_1_L2A` | Alqueva | before | 2018-08-23 11:30:36 | 05.00 | 0.285367 |
| `S2A_29SNC_20250823_0_L2A` | Alqueva | after; control after | 2025-08-23 11:30:58 | 05.11 | 0.009678 |
| `S2A_29SNC_20250803_0_L2A` | Alqueva | control before | 2025-08-03 11:31:00 | 05.11 | 0.006238 |
| `S2B_29SNB_20180823_1_L2A` | Neves-Corvo | before | 2018-08-23 11:30:50 | 05.00 | 0.001241 |
| `S2B_29SNB_20250826_0_L2A` | Neves-Corvo | after; control after | 2025-08-26 11:30:57 | 05.11 | 0.050947 |
| `S2A_29SNB_20250803_1_L2A` | Neves-Corvo | control before | 2025-08-03 11:31:15 | 05.11 | 0.188745 |

Source: `<case>/robustness.json`, keys `date_pairs.second_pair.items` and `manifest.inputs.stac.items[]`. All relative orbit 037.

## C.4 Same scenes on Microsoft Planetary Computer (provider check, Alqueva)

| Scene | Earth Search id | Planetary Computer id | Item time (UTC) | Processing baseline | eo:cloud_cover (%) |
|---|---|---|---|---|---|
| before | `S2A_29SNC_20180818_1_L2A` | `S2A_MSIL2A_20180818T112111_R037_T29SNC_20201011T032718` | 2018-08-18 11:21:11 | 02.12 | 0.073039 |
| after | `S2C_29SNC_20250821_0_L2A` | `S2C_MSIL2A_20250821T112131_R037_T29SNC_20250821T150517` | 2025-08-21 11:21:31 | 05.11 | 0.006082 |

Source: `alqueva_olive/interop_planetary_computer.json`, key `scenes[].planetary_computer`. The two providers give different item times for the same acquisition.

## C.5 Reference map

| Item | Value | Source |
|---|---|---|
| Name | Carta de Uso e Ocupação do Solo (COS) Série 2, editions 2018v4 and 2025v1, Direção-Geral do Território (DGT) | `reference_cos.json` `reference.name` |
| Service | DGT OGC API - Features, collections `cos2018v4` and `cos2025v1` | `reference_cos.json` `reference.service`, `reference.collections` |
| Licence | CC-BY (dados.gov.pt) | `reference_cos.json` `reference.license` |
| Polygons in the Alqueva study area | 183 (2018v4), 193 (2025v1) | `alqueva_olive/reference_cos.json` `reference.polygons_2018`, `reference.polygons_2025` |
| Polygons in the Neves-Corvo study area | 230 (2018v4), 231 (2025v1) | `neves_corvo_mine/reference_cos.json` `reference.polygons_2018`, `reference.polygons_2025` |
| Minimum mapping unit | 0.5 ha for both editions | `reference_cos.json` `caveats[1]`; DGT COS Série 2 specification [R268] |
| Production | Photo-interpretation of orthophotos by DGT; not derived from this pipeline | `reference_cos.json` `reference.independence` |
