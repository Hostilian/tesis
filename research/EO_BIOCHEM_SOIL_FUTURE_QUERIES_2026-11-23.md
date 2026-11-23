# Biochemistry / soil-chemistry feasibility queue — 23 Nov 2026

**Purpose:** Preserve every candidate research thread raised during thesis discussions; run evidence-first feasibility checks before scope changes or model training.

**Decision policy:** Existing three supervisor-approved space-based-economic-intelligence questions remain intact. This file is not a task calendar or a claim of complete evaluation. Record source IDs, raw evidence, collection date, independent evaluation, failed assumptions and reviewer decisions. Mark blocked work BLOCKED, not done. No private agricultural coordinates or supplier data in this public file.

Related: [scientific and market screen](BIOCHEM_EO_MARKET_AND_VALIDATION_2026-11-23.md) · [statistics consultation](STATISTICS_CONSULTATION_2026-11-23.md) · [validation gaps](../THESIS_VALIDATION_GAPS.md).

| ID | Candidate research query / falsifiable work item | What would count as evidence | Status as of 23 Nov |
|---|---|---|---|
| EO-01 | Are Sentinel-2 red-edge B05/B06/B07 bands accessible and useful for plant chlorophyll indices in Portugal? | Real STAC product IDs, 20 m native assets, pixel retrieval, QA, temporal coverage | **PARTIAL**: official specification + one observed public Chile scene's STAC assets; Portugal pixel read pending |
| EO-02 | Can open Sentinel-2 distinguish almond-tree canopy seasonal phenology from true crop stress? | Cloud-masked seasonal public time series, field-level reference, disjoint-year or field holdout, baseline | PENDING |
| EO-03 | Can measured leaf chlorophyll (e.g. chlorophyll meter/lab pigments) be estimated from NDRE/red-edge or radiative-transfer indices? | Independent matched lab samples, correctly aligned 20 m pixels, uncertainty, baseline | PENDING |
| EO-04 | Can independently measured almond foliar nitrogen be predicted from Sentinel-2 plus plant traits? | Two-orchard/independent-date calibration and test; field sample permits; compare published 2024 almond study | PENDING |
| EO-05 | Can leaf nutrients other than nitrogen (P/K/B/Mg) be remotely predicted beyond seasonal/canopy proxies? | Specific laboratory assay, measured signal and out-of-farm validation; reject unsupported analytes | PENDING / HIGH-RISK |
| EO-06 | Can canopy moisture/water stress be distinguished from nutrient deficiency, disease and management cycles? | Independent water-potential/soil-water measurements and negative controls | PENDING |
| EO-07 | When does 20 m red-edge resolution fail for mixed almond-canopy pixels or narrow rows? | Tree-spacing, canopy-cover fractions, georeferencing error, drone resolution comparison on allowed plots | PENDING |
| EO-08 | Which free satellite bands remain useful under real Alentejo cloud and revisit constraints? | Actual seasonal STAC search results and cloud-masked usable dates (not nominal 5-day revisit alone) | PENDING |
| EO-09 | Does multisource Sentinel-1 SAR + Sentinel-2 optical improve anomaly detection? | Correct SAR preprocessing, held-out biological ground truth and simple baseline | PENDING |
| EO-10 | Do authorized drone / crewed-aircraft orthomosaics add real, independent predictive value over optical-only features? | Legal data rights, matched acquisition dates, georeferenced imagery and ablation | BLOCKED on permission/data |
| SOIL-01 | Can the EU LUCAS 2018 topsoil lab data be lawfully accessed for a bachelor's research experiment? | EU registration, license acceptance and sample schema with legally permitted processing | PENDING; official registration required |
| SOIL-02 | Are LUCAS 2022 soil observations currently accessible? | Official dataset release and licensing | **NOT PUBLICLY RELEASED** at current official stated first-quarter 2027 estimate |
| SOIL-03 | Can Sentinel-2 bare-soil reflectance plus environmental covariates estimate laboratory soil organic carbon (SOC) in held-out EU regions? | Distinct site holdout; MAE/RMSE/R² with baseline; bare-soil controls, depth, uncertainty | PENDING |
| SOIL-04 | How much soil-SOC predictive skill is preserved after removing terrain, climate, old soil maps and spatial-coordinate leakage? | Ablation (no imagery / imagery / environmental layers) on spatially separated independent samples | PENDING |
| SOIL-05 | Can models predict SOC in remote unsampled regions, and know when to abstain? | Spatial domain-shift tests across soil types, crop types, management, climate; uncertainty calibration and abstention threshold | PENDING |
| SOIL-06 | Can pH/nitrogen/phosphorus/potassium be predicted from satellite imagery with genuine out-of-region skill? | Analyte-specific independent lab ground truth, improved baseline, limits; no blanket chemical inference | PENDING / HIGH-RISK |
| SOIL-07 | Is satellite reflectance a direct measure of soil chemistry beneath tree canopy? | Physical spectral model and bare-soil exposure verification | **NO direct subsurface measurement**; indirect contextual predictions only |
| SOIL-08 | Do tree-crop conditions in Alentejo yield enough bare-soil observations for SOC mapping? | Field exposure fractions, multi-date bare soil mask, dust/crop residue assessment | PENDING |
| SOIL-09 | Does the open AlphaEarth-soil-carbon or EUSO method already solve the same mapping problem? | Reproduce open baselines, external datasets and performance limits | PENDING |
| WATER-01 | Can PACE / Sentinel-3 / suitable Sentinel-2 data estimate chlorophyll-a in Portuguese water bodies? | Sufficient water-body size, independently matched in-situ chlorophyll, atmospheric correction | PENDING |
| WATER-02 | Can remote sensing distinguish dangerous algal toxins from high chlorophyll? | Target toxin assays and specificity study; avoid direct toxin claims | HIGH-RISK / NO DIRECT MEASURE |
| ATM-01 | Can public S5P methane/NO2 retrievals identify regional emission changes without falsely attributing individual sources? | Official source masks, footprint and ground/meteorological validation | PENDING |
| BIO-01 | Can EO data support biodiversity / ecosystem phenology forecasts without claiming taxonomic identification? | Independent land/field ecological survey and long-term observations | PENDING |
| FIN-01 | Do validated environmental indices incrementally predict independently observed economic output with realistic publication lag? | Official outcomes, out-of-time holdout, baseline, uncertainty | PENDING |
| FIN-02 | Does a putative biochemical EO indicator deliver tradable hedge-fund alpha? | Point-in-time release dates, genuine out-of-sample net-of-cost returns and no look-ahead | **NOT ESTABLISHED** |
| GOV-01 | Is any proposed extension compatible with original thesis and supervisor permission? | Explicit signed/recorded supervisor agreement | PENDING |
| GOV-02 | Can the science be verified without private farm geodata / commercial imagery? | Public sources or permissioned private pipeline plus non-identifying aggregate report | PENDING |
| GOV-03 | Have numerical results been independently audited rather than copied from mock demo? | Reproducible real source IDs, independent labels, script/seed, held-out metrics | NOT SATISFIED |
| MARKET-01 | Who buys validated orchard/nutrient/soil decisions versus already pays for existing monitoring? | Named budget owner, current expenditure, documented pain, substitute comparison | NO BUYER RECEIPT |
| MARKET-02 | Do users pay for *validation + provenance + abstention* rather than generic vegetation maps? | Concrete requested deliverable, paid pilot or purchase receipt (user approval before outreach) | UNKNOWN |
| MARKET-03 | Can existing open source (PySTAC, eo-learn, ODM, RTM-Suite, SpectroChemPy) do this already? | Reproduce reference workflows, compare marginal value, explicit license/cost checks | PARTIAL: repositories exist; no end-to-end test |
| MARKET-04 | Does the VenturaAtlas/OMEGA evidence ladder justify a commercial decision? | Buyer activation/budget/purchase-event receipts plus independent technical and legal validation | NO: keep UNVALIDATED |
| EMAIL-01 | Complete review of stored visas/wallet/university/work/support drafts with translations and duplicate guard | Readback from Gmail and private review inventory; no send | IN PROGRESS; off-repo/private only |

### Next independent test gates

**Plant first:** (1) confirm a public Portugal scene containing 20 m B05-07 and SCL; (2) retrieve actual pixels via rasterio/stackstac, record hashes; (3) verify real field chemistry sample access; (4) compute seasonally controlled simple baselines; (5) blind held-out orchard/year assessment; (6) publish uncertainty and explicit failure cases.

**Soil separately:** (1) accept LUCAS license or find alternative open lab source; (2) verify chemical analyte/depth/date and legal geometry; (3) bare-soil composite; (4) coordinates/site-disjoint holdout; (5) compare environmental-only baseline to satellite-added model; (6) test geographically new regions; (7) abstain when remote site is outside source-domain coverage.

**Preserved but not adopted:** aquatic pigments, waterborne toxin-specific skepticism, biodiversity, atmospheric composition, economic indicators, and finance-market hypotheses. No one is dropped merely because another becomes the first experiment.

### Important current evidence

- Published public STAC item: `S2B_MSIL2A_20241004T143749_R096_T19KEQ_20241004T183052` returned metadata for B05/B06/B07 (each 20 m) and SCL via `GET https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/<id>` on **23 Nov 2026**; **this is a Chile scene, not an Alentejo sample, and the metadata check is not a new pixel read**.
- The 19-Nov [three-region observed proof](../docs/data/observed_three_region_proof_20261119.json) verifies real B02/B03/B04/B08/B11 pixel ingestion, not red-edge imagery or chemistry prediction.
- The official [LUCAS 2018 registration page](https://esdac.jrc.ec.europa.eu/content/lucas-2018-topsoil-data) provides a lab-linked option, subject to terms. [LUCAS 2022](https://esdac.jrc.ec.europa.eu/content/lucas-2022-topsoil-data) currently projects public availability in 2027.
- Published [almond nitrogen study](https://ishs.org/ishs-article/1395_20/) reports R² values of 0.79 (2020) and 0.72 (2021), **not this project's independent metrics**.
- [European SOC satellite-LUCAS study](https://www.sciencedirect.com/science/article/pii/S0016706124003422), [multi-site soil texture caveat](https://bsssjournals.onlinelibrary.wiley.com/doi/10.1111/ejss.70054), [bare-soil limitations](https://www.mdpi.com/2072-4292/17/4/630) and [soil profile limits](https://irc-orcasa.eu/wp-content/uploads/2025/08/ORCaSa_D4.2_Monitoring-Reporting-and-Verification-of-soil-organic-carbon-stock-changes-at-arable-land_-Disclaimer-version.pdf) motivate spatial holdouts and conservative interpretation.

**Do not schedule automated reminders or make outbound contact from this research file; it is a durable query backlog, not a running automation.**
