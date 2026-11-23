# Soil Earth-observation venture ranking — 23 November 2026

**Status:** Analyst hypothesis ranking; no independent customer payment or proof of laboratory replacement; no external emails sent. Preserve current thesis research questions until supervisor approval.

## Decision method
Open-source [`PyMCDM 1.4.0`](https://github.com/kotbaton/pymcdm), MIT-licensed. The TOPSIS and WSM calculations and seeded sensitivity trials are [reproducible](venture_rankings/rank_soil_opportunities.py), with [machine-readable results](venture_rankings/rank_results_20261123.json). Criteria weights: 23% scientific defensibility, 16% laptop feasibility, 20% buyer trigger, 13% possible differentiation, 12% starting without laboratory records, 10% career fit, 6% speed. Ratings are subjective 0–10 decisions, not measured probabilities.

## Results

| Rank | Candidate | TOPSIS preference | Science/solo/buyer/differentiation/data/career/speed | Top under weight changes (200) | Top under score uncertainty (400) |
|---:|---|---:|---|---:|---:|
| 1 | EU Soil Evidence Pack | 0.889 | 9/8/8/5/8/9/7 | 189 | 177 |
| 2 | Surface Sealing/Removal Change Audit | 0.822 | 9/9/8/4/9/8/9 | 11 | 142 |
| 3 | Soil Sampling Priority Map | 0.760 | 8/9/7/4/7/9/8 | 0 | 35 |
| 4 | Bare Soil / Erosion Exposure Alert | 0.745 | 8/9/7/4/8/8/9 | 0 | 29 |
| 5 | Water Pigments / Bloom QA | 0.677 | 7/8/7/4/7/8/7 | 0 | 7 |
| 6 | Habitat / Phenology Change Watch | 0.660 | 8/9/6/4/9/8/9 | 0 | 6 |
| 7 | Lab Sample Provenance + Satellite QA | 0.640 | 9/9/6/4/5/8/7 | 0 | 4 |
| 8 | Orchard Pigment / Lab Calibration | 0.620 | 6/8/7/4/4/9/6 | 0 | 0 |
| 9 | Satellite Surface Moisture Triage | 0.536 | 6/8/6/4/8/7/7 | 0 | 0 |
| 10 | Surface Salinity Risk Screening | 0.515 | 5/7/6/5/6/8/6 | 0 | 0 |
| 11 | Carbon Maps for Unsampled Land | 0.455 | 4/7/7/3/3/9/5 | 0 | 0 |
| 12 | Bio-chemical Economic Forecasting | 0.193 | 3/5/5/3/4/8/4 | 0 | 0 |
| 13 | Lab Nutrients and pH Replacement | 0.151 | 1/5/6/3/2/7/3 | 0 | 0 |

**Why each ranks as shown; exact competition and scientific barriers**

### 1. EU Soil Evidence Pack

EU Soil Monitoring Law creates an evidence workflow; CLMS already supplies free mapping and Spacenus sells verification. Wedge: reviewer-ready provenance and uncertainty, not new chemical inference.

### 2. Surface Sealing/Removal Change Audit

Surface change has a direct optical signature and policy use. Weak differentiation: free CLMS imperviousness 10m and existing EEA products.

### 3. Soil Sampling Priority Map

Satellite covariates can prioritize physical lab collection, not replace chemistry; exact ESA NAVISP / SOCBIO-MAP and QGIS Field Guide compete.

### 4. Bare Soil / Erosion Exposure Alert

Fast on existing data and plausible review value, but Trends.Earth and JRC erosion products are free substitutes.

### 5. Water Pigments / Bloom QA

PACE/operational aquatic monitoring support scientific matchup review, but CyAN/NASA services serve many use cases already.

### 6. Habitat / Phenology Change Watch

Clear satellite observable, but FAO Open Foris and CLMS coverage undermine a generic product pitch.

### 7. Lab Sample Provenance + Satellite QA

Traceability is measurable and laptop-friendly; needs permissioned lab samples and must differentiate from SoloMapa, 4 Farm, NAVISP.

### 8. Orchard Pigment / Lab Calibration

Real red-edge assets and NDRE technically proven in public Alentejo scene, but no site-matched lab labels and commercial nitrogen competitors exist.

### 9. Satellite Surface Moisture Triage

Valid proxies available, but terrain/vegetation effects impair local moisture truth; Copernicus soil moisture data substitute.

### 10. Surface Salinity Risk Screening

Potential visible salts and soil reflectance, but site-specific lab calibration needed; cannot assume chemistry levels.

### 11. Carbon Maps for Unsampled Land

Portugal independent R2=0.44, spatial CV R2=0.34; cannot call predictions equivalent to laboratory data or SOC accreditation.

### 12. Bio-chemical Economic Forecasting

Point-in-time economic data matching and leakage avoidance would be expensive; market need and alpha unknown.

### 13. Lab Nutrients and pH Replacement

Sentinel-2 cannot directly measure P, K, pH or contamination concentration beneath soil. Reject 90% lab replacement without true tests.

## Scientific 90% reliability acceptance

- An R² of 0.9 is **not** 90% correct laboratory results; a 90% prediction-interval coverage can be so wide that it is not useful. Require a prespecified soil-analyte-specific tolerance, MAE/RMSE, independent farm/location and year holdouts, confidence interval calibration, and abstention where the site differs from calibration conditions.
- **Technically automatable without lab tests:** obtaining Sentinel imagery; plotting surface sealing/removal or bare soil; comparing historic scenes; producing parcel-level provenance reports; and selecting review or laboratory sampling priority. This is not replacing a legally required physical test or a certified contaminant assessment.
- An aspirational >=90% sensitivity benchmark can be established for **field-verified surface-change classification** in a bounded test set, with an explicit false alarm rate and independent ground reference; not achieved yet.
- Lab nitrogen, pH, P/K, contaminated soils and sub-surface carbon still require independently measured values for reliable property-specific outputs. Soil monitoring predictions can only be conditional screening, with calibrated error.
- LUCAS 2018 lab soil sample locations are **licensed and not representative of individual fields**; do not copy data into public repositories or claim certainty for unsampled fields.

## Actual competition and possible narrow product

- [Copernicus CLMS Imperviousness 2024](https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness/imperviousness-density-2024) offers free 10m/100m mapped land sealing; do not replicate and resell unchanged.
- [ESA SOCBIO-MAP](https://business.esa.int/projects/socbio-map) describes satellite-optimized soil sampling + lab analysis + carbon mapping with existing partners and ESA backing. Advertised 30–50% fewer samples is its claimed project objective, **not** an independently verified outcome.
- [ESA NAVISP Smart Sampling Platform](https://navisp.esa.int/project/306-smart-analytics-platform-for-agricultural-sampling) already works on georeferenced farm sample planning, traceability and integration.
- [Spacenus](https://spacenus.com/), [SoloMapa](https://sysall.com.br/en/consultor/index.html), [4 Farm](https://4farm.app/), [ESA SoilEO](https://business.esa.int/projects/soileo) offer overlapping soil/nutrient/satellite workflows.
- Free alternatives: [FAO Open Foris](https://www.openforis.org/), [Trends.Earth](https://www.unesco.org/en/unesco-digital-innovation-hub/trendsearth-qgis-plugin), [SoilGrids](https://isric.org/explore/soilgrids/), [QGIS Field Guide](https://plugins.qgis.org/plugins/fieldguide/).
- **Possible testable wedge:** independent provenance/quality-control layer that shows source scene, timestamps, scene cover, conflicting samples, uncertainty and whether a field review or legally adequate lab sample remains necessary. This must be purchased by a real buyer to qualify as a business.

## Buyer evidence and funding, fail-closed

- [EU Directive 2025/2360](https://environment.ec.europa.eu/topics/soil-health/soil-monitoring-law_en) came into force 16 Dec 2025, explicitly supports Copernicus for soil sealing/removal, and still requires periodic soil sampling. National transposition due Dec 2028. It is policy demand, **not** a procurement contract for our product.
- The [EUSPA 2026 market report](https://www.euspa.europa.eu/market-report) estimates global EO revenue €3.5bn in 2024, rising to €7.9bn 2034. Not the serviceable market for this idea.
- Official [CLMS work opportunities](https://land.copernicus.eu/en/work-opportunities) and [JRC satellite land monitoring tender](https://land.copernicus.eu/en/news/the-european-commissions-joint-research-centre-jrc-launches-a-new-tender-for-clms-global-satellite-based-land-monitoring-services) show procurement exists, but government framework tenders may require consortia, legal entities, qualifications and multi-year delivery.
- [ESA BIC Centro](https://space.ipn.pt/apply/) can provide up to €60k in equity-free funding for a company with a space-data connection. Applicants can begin before incorporation, but must incorporate in Portugal before signing, and at least one authorized representative must have **permanent Portuguese residence**. The researcher's eligibility is not established; funding is not awarded.
- No paid pilot, named buyer, signed letter of intent, purchase order, budget owner, validated scientific model or business sale was obtained. **Do not promote ideas to SELL_NOW or imply a bid has been submitted.**

## Laptop-only execution / falsification order

1. Reuse existing public real Alentejo [red-edge proof](../docs/data/observed_alentejo_rededge_20261123.json) and [source code](prototypes/rededge_real_pixel_preview.py). Do not claim chemistry prediction.
2. Obtain independent public evidence for 50–100 distinct sites in one geographic region and compare CLMS 2024 against earlier maps, with aerial/human source reference; check false positives and negatives.
3. Render a static map, case-evidence JSON/GeoJSON and short reviewer-ready PDF; CPU and open data only.
4. Evaluate lab-sampling priority against random and standard sampling *only after* getting lawfully authorized real lab records.
5. Draft buyer questions for municipality/soil consultancy/audit firm and check budget/process; no outreach unless the user explicitly approves an individual message.
6. If free CLMS/QGIS already provides equivalent answers in minutes, or no paid buyer exists, abandon the generic evidence pack and keep the verified technical work as thesis evidence.

## Continuity
Original [statistics consultation](STATISTICS_CONSULTATION_2026-11-23.md), [soil/biochemistry science review](BIOCHEM_EO_MARKET_AND_VALIDATION_2026-11-23.md), [unanswered future query backlog](RESEARCH_QUERY_BACKLOG_2026-11-23.md), [webpage](../docs/research-questions.html). Existing visa, wallet, Évora academic and farm tasks are not superseded by this study. No messages sent.
