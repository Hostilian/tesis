# Satellite biochemistry, biological monitoring and market validation — evidence review

**Research date:** 23 November 2026. **Evidence type:** independently sourced desk research + source-code inspection + open-source repository existence checks. **Status:** exploratory; **not** an approved thesis-scope change, not a customer validation study, and not a real-data scientific evaluation.

> Decision boundary: **research first; reuse before building; preserve before modifying; verify before claiming.** No supplier credentials, private farm coordinates, personal correspondence, or nonpublic laboratory rows belong in this public note.

## Executive decision

**Keep the existing supervisor-approved thesis:** *Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs*. Its approved research direction covers anomaly-ground-truth reliability, VIIRS–economics relationships, and open-API pipeline constraints. Candidate biology/chemistry applications can use exactly the same backbone (source APIs → reflectance/QA → features → baseline/model → independent measurements → provenance-aware decision support). Any amendment needs supervisor agreement.

**Strongest applied candidate:** agronomic **biochemical-indicator validation** in Portugal (chlorophyll proxy, canopy water-condition proxy, lab leaf/soil observations, drone/aircraft cross-resolution support), only where written data permissions and site-matched independent samples exist.

**Strongest open scientific alternative:** aquatic chlorophyll/phytoplankton indicators with NASA PACE, Sentinel-3, and suitable independent water samples. **Strongest chemistry-data alternative:** EU LUCAS soil laboratory samples joined cautiously with public Sentinel-2 bare-soil observations.

**Commercial verdict:** neither buyer payment, purchase order, renewal, willingness-to-pay, budget owner, nor pilot contract has been evidenced for *this proposed product*. External market revenues and competitors are evidence of an existing category, not proof that a new entrant would sell. Under VenturaAtlas / OMEGA fail-closed rules: **NOT COMMERCIALLY VALIDATED / NO PROMOTION**.

## 1. Existing thesis questions — unchanged

- **RQ1:** How reliably can open satellite spectral APIs identify localized industrial and mining resource anomalies compared to ground truth records?
- **RQ2:** What is the correlation between VIIRS night-time light fluctuations and macro/microeconomic indicators in the target regions?
- **RQ3:** What pipeline latency and processing constraints limit the scalability of free satellite APIs for real-time economic monitoring?

Source: [thesis introduction](../thesis/chapters/01_introduction.md). The [statistics consultation agenda](STATISTICS_CONSULTATION_2026-11-23.md) records eight empirical-design questions. Do not silently substitute new RQs or claim the proposed biology direction is registered.

## 2. Scientific sensor and ground-truth feasibility

| Proposed physical indicator | What satellite measures | Claim ceiling | Independent evidence required | Source |
|---|---|---|---|---|
| Plant chlorophyll / pigment | Reflected spectral radiance, especially Sentinel-2 visible/red-edge, algorithmic chlorophyll proxies | **Conditional estimate** of canopy/leaf pigment, not a blood test of leaves | Field chlorophyll meter, leaf pigment laboratory measurements, paired plot/date/scale | [ESA plant health](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/Plant_health), [global chlorophyll validation, Scientific Data](https://www.nature.com/articles/s41597-025-05831-x) |
| Foliar nitrogen / orchard nutrient stress | Pigment, water and structural correlates of N | **Indirect proxy**, no unique attribution to N deficiency | Calibrated foliar N lab assays + water, canopy, season controls | [critical review 2026](https://www.mdpi.com/2072-4292/18/18/3093), [soil/crop nitrogen review](https://www.mdpi.com/2504-3129/7/3/82) |
| Soil carbon / chemistry (pH, P, N etc.) | Surface reflectance when **bare soil** is exposed; spatial covariates | Cannot directly infer chemistry beneath ground or independently estimate every analyte | Georeferenced measured soil samples, depth, dry/bare-soil dates, local validation | [European SOC research](https://www.sciencedirect.com/science/article/pii/S0016706124003422), [LUCAS 2022](https://esdac.jrc.ec.europa.eu/content/lucas-2022-topsoil-data) |
| Water chlorophyll and phytoplankton pigments | Water-leaving reflected radiance / ocean color | Algorithmic pigment/biogeochemical estimates, **not toxin or DNA assays** | In-situ pigment/chlorophyll lab measurements and matchup protocol | [NASA PACE BGC](https://pace.oceansciences.org/pace_bgc_oci.htm), [NASA PACE field validation](https://nasa.github.io/oceandata-notebooks/faq.html) |
| Ecosystem habitat and phenology | Land cover/seasonal vegetation response | Habitat condition indicator, **not identification of every organism/species/microbiome** | Field transects/ecological inventories and spatial support checks | [CLMS vegetation](https://land.copernicus.eu/en/products/vegetation) |
| Methane / NO2 | Column concentrations/absorbing gases | Gas signals at instrument-specific detection/footprint scales, **not arbitrary individual-source attribution** | Independent ground observations, meteorology, plume method | [Copernicus Sentinel-5P](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-5p) |
| Biochemistry of DNA, pesticides, individual proteins | Not directly observable by conventional optical 10–30 m satellite bands | **No direct remotely sensed molecular assay** | DNA/sequencing and analytical lab test; satellite only as spatial covariate | [LUCAS soil + eDNA/pesticide residues measured in laboratories](https://esdac.jrc.ec.europa.eu/content/lucas-2022-topsoil-data) |

**Negative scientific benchmark:** A published global Sentinel-2 chlorophyll product reported **R² = 0.37** and **RMSE = 13.69 μg/cm²** against its ground validation (not a universal bound for other studies). Do not substitute studies reporting high within-crop fit for site-independent performance. Source: [Scientific Data 2025](https://www.nature.com/articles/s41597-025-05831-x).

**Resolution correction:** Sentinel-2 common visible/NIR bands (e.g. B04 and B08) have 10 m native resolution, while red-edge B05/B06/B07 have **20 m** native resolution. Regridding to 10 m does not create new red-edge spatial information. Source: [official band documentation](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html).

**Restricted/open distinction:** The EU LUCAS 2022 portal specifies licensee / organizational-access terms for its soil database. A listed chemistry/eDNA variable does **not** mean anonymous, free and unrestricted machine-readable samples or field coordinates are available. Check explicit license and acquisition conditions before use. [ESDAC terms](https://esdac.jrc.ec.europa.eu/content/lucas-2022-topsoil-data).

## 3. Source-code audit against the proposed biochemical use

**23 November addendum — successful public real-pixel red-edge preview:** The separate [reproducible pilot](prototypes/rededge_real_pixel_preview.py) read an actual public Alentejo Sentinel-2B scene's B05/B06/B07/B8A spectral assets (plus B04/B08/SCL). The signed COG images yielded **9,216 quality-masked analysis-grid pixels**, median **NDRE 0.2127** and **NDVI 0.2621**; [proof JSON](../docs/data/observed_alentejo_rededge_20261123.json) records the source scene and checksum. This validates source availability and spectral-index arithmetic, **not independently measured leaf chlorophyll/nitrogen**, and does not modify the main production ingestion route. The data come from an unspecified public Alentejo sampling window, not proprietary farm information.

**Observed code**, inspected 23 November 2026: [Planetary Computer live pixel reader](../pipeline/planetary_observation.py) uses mapping B02, B03, B04, B08, B11 and scene classification (SCL), reading a bounded 96x96 real-pixel preview. It **does not currently ingest red-edge B05, B06, B07, or a calibrated foliar assay**; it does not have time-series reference-label evaluation.

- Keep the existing fail-closed source reader and synthetic demo separate.
- If supervisor approves a biochemical pilot, **adapt** the existing source reader to include B05/B06/B07 using native 20 m-aware geospatial alignment with an explicit effective spatial-support statement.
- Prefer standard, validated red-edge index and radiative-transfer methods over bespoke chemistry inference.
- Check SCL/quality masks, atmospheric corrections, scene IDs, processing baseline, timestamps, pixel-grid provenance, uncertainty and measured plot matching.
- Place approved private Rota Única data **only** in a permitted private environment; never copy farm-boundaries, privileged images, lab records, tokens or device identities here.
- The three-region 21,253 observed Sentinel-2 pixels documented in [observed proof](../docs/data/observed_three_region_proof_20261119.json) show ingestion feasibility **only**, not biochemical prediction or external labels.
- Do not upgrade historical F1 = 0.907 or r = 0.724 to validated claims; see [validation gaps](../THESIS_VALIDATION_GAPS.md).

## 4. Candidate research tracks and tests

### A — Portugal orchard condition × leaf chemistry (priority applied case)

**Researchable question:** *Do seasonally controlled Sentinel-2 red-edge and water-content indicators explain variation in independently measured leaf chlorophyll/nitrogen or agronomic stress at the orchard-block scale, and does approved drone/aircraft context improve out-of-sample performance over a satellite-only baseline?*

- **Unit:** orchard block or matched plot × observation date; never claim individual-tree resolution from 20 m red-edge assets.
- **Methods:** NDVI/NDMI and seasonal baseline first; add CIred-edge/NDRE only after correct band import; potentially compare Isolation Forest to rolling median/MAD and physically interpreted indices.
- **Ground truth:** authorized lab leaf analysis/foliar N, sampling coordinates generalized into approved block keys, sampling time, calibrated measurement; perhaps plant water potential if independently measured.
- **Failure/kill:** no independent assays with matched times/blocks; mixed pixels dominate plots; no authorized datasets; improved model does not outperform seasonal baseline on held-out blocks.
- **Use case:** farm diagnostics and reproducible data quality, **not** fertilizer dosage prescription or automatic biological diagnosis.

### B — Portugal water-body phytoplankton and chlorophyll

**Question:** *Can open NASA PACE/Sentinel-3 ocean-colour products track chlorophyll-a variation in sufficiently large Portuguese water bodies and agree with independently sampled in-situ water chemistry?*

- Reuse [NASA oceandata notebooks](https://github.com/nasa/oceandata-notebooks) and [PACE data](https://pace.oceansciences.org/access_pace_data.htm), plus official [Portugal APA/SNIRH](https://apambiente.pt/agua/sistema-nacional-de-informacao-de-recursos-hidricos-snirh) monitoring records.
- **Key negative:** PACE ~1.2 km-scale water pixels and aquatic-optics limits may exclude small reservoirs; NASA states water bodies typically need at least ~10–25 km² for credible HAB monitoring at PACE scale. NASA explicitly requires in situ pigment observations for phytoplankton validation [NASA FAQ](https://nasa.github.io/oceandata-notebooks/faq.html).
- **Buyer substitutes:** US EPA [CyAN](https://www.epa.gov/water-research/cyanobacteria-assessment-network-application-cyan-app) already serves public-water bloom monitoring; do not describe bloom monitoring as a new unserved market.
- **Kill:** no water body large enough / no coincident laboratory records / no meaningful improvements beyond operational public products.

### C — European soil chemistry with satellite contextual prediction

**Question:** *Can traceable Sentinel-2 bare-soil spectra and environmental covariates predict held-out, laboratory-measured European soil organic carbon better than an openly reproducible simple baseline?*

- **Independent dataset:** [European Commission LUCAS soil](https://esdac.jrc.ec.europa.eu/content/lucas-2022-topsoil-data), subject to access/license.
- **Prior work:** [European SOC monitoring system](https://www.sciencedirect.com/science/article/pii/S0016706124003422); [LUCAS/AlphaEarth open-source comparator](https://github.com/michaelfburke/alphaearth-soil-carbon). This is an existing research field, **not** blank research space.
- **Negative:** bare-soil sparsity, topsoil-only visibility, sampling depth, nontransferability across soil types and weak temporal change validation. [Global open soil data/limitations](https://essd.copernicus.org/articles/18/989/2026/).
- **Kill:** sample terms inaccessible; signal weak across withheld sites; uncalibrated maps misleading.

### D — Biodiversity and ecosystem phenology

**Question:** *How reliably can open EO time-series detect habitat/phenology change against independent ecological monitoring in Portugal?*

- **Inputs:** Sentinel-2, [CLMS vegetation products](https://land.copernicus.eu/en/products/vegetation), authorized field ecological surveys.
- **Not claimed:** direct species counts, organism identity, soil microbiome or DNA.
- **Barrier:** geographic and seasonal bias, sparse independent field inventories, free publicly available indicators.

### E — Atmospheric chemistry and industrial emissions

**Question:** *How reproducibly can open satellite atmospheric composition APIs flag regional methane or nitrogen dioxide variations, with defensible uncertainty and independent validation?*

- Use [S5P collection](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-5p) with [HARP harmonization](https://atmospherictoolbox.org/harp/). NASA [EMIT](https://earth.jpl.nasa.gov/emit/) maps surface mineral spectra and can detect some methane plumes under suitable conditions.
- **Limit:** emission source attribution, instrument footprint, meteorology, retrieval uncertainty, commercial incumbents; no molecule-agnostic chemical detector.

### F — Investment/hedge-fund research track (deferred, independent of thesis claim)

**Question:** *Does an Earth-observation-derived agricultural/chemical indicator provide incremental, out-of-sample forecasting information about publicly reported production or economic indicators after removing ordinary seasonality?*

- Potential **academic research**, not evidence that a trading strategy has alpha or that a hedge fund needs this product.
- Start with economic prediction vs official observations, not trading. If later exploring returns, check point-in-time data availability, publication lags, commodity exposure mapping, look-ahead leakage, transaction costs, market beta, survivorship and realistic delayed execution.
- **Commercial moat unproven:** alternative-data firms, institutional analysts, publicly available Copernicus indicators and existing signal vendors are substitutes.
- No backtested alpha, investment advice, fund demand or customer payments are asserted.

## 5. Industry demand and contradiction register

**Primary market signal (category, not addressable market):** EUSPA's [2026 EU Space Market Report](https://www.euspa.europa.eu/market-report) lists **€3.5bn global EO revenue in 2024** and forecasts about **€7.9bn by 2034**. It reports that **agriculture** had **21% of EO revenue in 2024**. This is a forecast/category statistic, *not* a chemical satellite product TAM, prospective buyer count, or promise of expenditure.

**Known competitors and substitutes:**
- [SatAgro](https://satagro.net/) offers operational crop monitoring, machinery/IoT integration, and farm-management tools.
- [EOSDA services](https://aws.amazon.com/marketplace/pp/prodview-rv6ieakd626cw) package satellite crop monitoring/classification/yield prediction; a listing is evidence of supply, **not purchase count**.
- [NASA's operational PACE processing](https://github.com/nasa/oceandata-notebooks), [EPA CyAN](https://www.epa.gov/water-research/cyanobacteria-assessment-network-application-cyan-app), and [CLMS vegetation products](https://land.copernicus.eu/en/products/vegetation) are excellent free substitutes.
- [ESA RegenAg–MRV](https://business.esa.int/projects/regenag-mrv) reports two customer partnerships after a 2026 pilot; this shows a related commercial application but not buyer proof for this project.
- [ESA 2026 water-sector call](https://business.esa.int/funding/call-for-proposals-non-competitive/digitalisation-water-sector) calls for user letters of intent, demonstrating a real requirement for user engagement rather than software novelty.

**Disconfirming evidence:**
1. **Scientific false positives:** independently validated Sentinel-2 global chlorophyll R² 0.37 (above), and correlated vegetation/pigment/water signals make causal attribution difficult.
2. **Buyer budget/practical barriers:** [2025 European public-authority EO uptake study](https://www.mdpi.com/2413-8851/9/11/489) finds skills, budgets and inadequate resolution/information as important blockers.
3. **Market/payer mismatch:** [ECDPM 2026 report](https://ecdpm.org/work/satellites-services-financing-earth-observation-public-value) describes many EO pilots failing to become durable operations because payer and beneficiary differ and operating budgets do not follow grants.
4. **Policy timing instability:** EU [2026 sustainability reporting simplification](https://www.consilium.europa.eu/en/press/press-releases/2026/02/24/council-signs-off-simplification-of-sustainability-reporting-and-due-diligence-requirements-to-boost-eu-competitiveness/) undermines any pitch that assumes unchanged mandatory reporting pressure.
5. **Technological substitutes:** there are several mature open-source toolchains and commercial offerings; a generic NDVI dashboard has no evidence of competitive differentiation.
6. **Commercial evidence absent:** no named willing buyer, pain-cost receipt, paid pilot, valid letter of intent or procurement decision has been obtained for any proposed new product in this research.

**Possible non-generic gap to test (hypothesis):** a **calibration- and provenance-aware bridge between existing satellite indicators and independently measured agricultural biochemistry**, especially reliable *negative* outputs that say what cannot be concluded. This is **not** proven whitespace; it requires direct buyer and independent-sample tests.

## 6. Reuse-first verified open-source stack

Existence and non-archived status of the following GitHub repositories were cross-checked through GitHub on 23 Nov 2026; **not** a claim they have been installed, benchmarked or licensed for every intended use:

| Role | Existing open source | What to reuse | Validation needed |
|---|---|---|---|
| Catalogue / real EO input | [PySTAC Client](https://github.com/stac-utils/pystac-client), [CDSE STAC API](https://documentation.dataspace.copernicus.eu/APIs/STAC.html) | Exact scene IDs and asset metadata | Imagery actually readable; no mock fallback |
| Optical time-series and ML | [eo-learn](https://github.com/sentinel-hub/eo-learn) | EO task processing, cloud masking, data cubes | Native-resolution and site-based cross-validation |
| Large remote sensing | [openEO](https://openeo.org/) and [CDSE API](https://dataspace.copernicus.eu/analyse/apis) | Official processing API instead of custom backend | Quotas, provider coverage and costs |
| Radiative transfer / biological pigments | [RTM-Suite](https://github.com/CCGCAM/RTM-Suite) | PROSPECT/SAIL radiative-transfer building blocks | Calibration to the target crop and geometry |
| Water pigments | [NASA ocean-data notebooks](https://github.com/nasa/oceandata-notebooks) | PACE OCI pigment processing and data access | In-situ pigment matchups |
| Spectroscopy / chemistry | [SpectroChemPy](https://github.com/spectrochempy/spectrochempy) | Laboratory spectral-analysis data structures | Not a tool that magically recovers pesticide DNA from Sentinel-2 |
| Drone/aircraft | [OpenDroneMap](https://github.com/OpenDroneMap/ODM) | Orthoimage/photogrammetry and CRS workflow | Data permission, geometry and calibration |
| Atmospheric composition | [HARP](https://atmospherictoolbox.org/harp/) | Harmonize S5P-type products | Retrieval quality and transport/meteorology |
| Soil carbon comparator | [AlphaEarth–soil carbon](https://github.com/michaelfburke/alphaearth-soil-carbon) | Existing public LUCAS-informed experiment | Dataset licensing, region-specific held-out check |

**Installation status in thesis:** do not treat any of these as an integrated tested dependency until a separate reproducible build/test passes.

## 7. VenturaAtlas / OMEGA external validity gate — bounded application

I inspected the existing [VenturaAtlas repository](https://github.com/Hostilian/VenturaAtlas) and its [12-round research contract](https://github.com/Hostilian/VenturaAtlas/blob/main/research/constitution/ORIGINAL_DEEP_RESEARCH_EXECUTION_CONTRACT.md), [OMEGA XIV capital clock](https://github.com/Hostilian/VenturaAtlas/blob/main/research/OMEGA_XIV_CAPITAL_CLOCK_2026-08-17.md), [OMEGA XIX evidence/competitor audit](https://github.com/Hostilian/VenturaAtlas/blob/main/research/audits/OMEGA-XIX-20260827T135453Z/ANTIGRAVITY_SPEC.md), and [OMEGA XXI negative-evidence protocol](https://github.com/Hostilian/VenturaAtlas/blob/main/research/omega-xxi/README.md).

**This is a deliberately bounded slice** for thesis directions, **not** a completed twelve-round venture investigation (the original process requires 60 distinct queries, 50 direct problems, 60 opportunity ideas, 12+ cost audits, paid tests, etc.; those gates have not been executed). Never mislabel it as completed.

| Venture gate | Current observation | Verdict |
|---|---|---|
| Research novelty | EO + biochemical traits already researched; specific reproducible orchard-to-lab workflow not yet demonstrated | Existing field; possible narrow implementation research |
| Legally usable data | Public Sentinel data accessible; LUCAS 2022 restrictions; Rota Única private consent unknown | PARTIAL / CONDITIONAL |
| Competitor map | SatAgro/EOSDA, Copernicus, NASA/EPA and literature open-source substitutes located | PASS for existence; not exhaustive |
| Evidence hierarchy | Official agency documentation and independent papers checked; vendor assertions kept separate | PASS for bounded literature screen |
| Demand / buyer budgets | Category revenue and commercial supply observed; named buyer/product budget unknown | UNKNOWN |
| WTP / sale / receipt | No direct payment, buyer commitment, or validated offer | FAIL — NOT COMMERCIAL VALIDATION |
| Paid acquisition cost | No actual vendor/support/hosting quote for proposed delivered service | UNKNOWN |
| Public/privacy permissions | Farm labs/imagery must remain private and permissioned | HARD GATE |
| Scientific claim | Observed pixels yes; validated bio/chem result no | FAIL until real matched labels |
| Competitive control point | Auditable satellite-to-lab lineage hypothesized; no buyer preference test | HYPOTHESIS |
| Financial strategy | No point-in-time economic forecast or out-of-sample trading backtest | NOT ESTABLISHED |
| Thesis proposal | Strong Informatics link, but official topic remains unchanged | CONSULT SUPERVISOR FIRST |

**No promotion to SELL_NOW, product-market fit, hedged return forecasts, operational warning thresholds or validated science.**

### Suggested seven-day <$20 desk validation, not an action taken

1. Scientific data spike: inspect one public Sentinel-2 scene; confirm B05/B06/B07 asset keys and non-synthetic reflectance values; document native 20 m geometry (no private farm geometry).
2. Matchup feasibility: request appropriate licensed LUCAS samples *or* locate a suitable independently sampled public water site. Do not assert access before granted.
3. Compare one fixed seasonal/baseline model against a more complicated model on **held-out independent units**, with reported missingness and uncertainties.
4. Buyer problem test (drafts only): identify a named agronomist, lab manager, water utility or remote-sensing decision maker; ask which existing paid tool they use, cost of false alarms and whether an independently validated report is worth a fee. No outreach without user approval; **a conversation is not a paid receipt**.
5. Falsification: if no field samples, no additional predictive value, or no actual paid problem, report the negative and keep thesis scope at reproducible source ingestion and quality assessment.

## 8. Four candidate supplemental questions (NOT replacing existing RQs)

- **BIO-Q1 — Plant pigments:** *Can an API-first Sentinel-2 red-edge time-series reproducibly explain measured variation in plant chlorophyll/foliar nitrogen across independent agricultural plots, with uncertainty and seasonality controls?*
- **BIO-Q2 — Water ecosystems:** *How consistently do open satellite pigment estimates correspond to independent in-situ water chlorophyll measurements across seasons and water types?*
- **CHEM-Q1 — Soil chemistry:** *Does adding properly masked Sentinel-2 bare-soil reflectance improve held-out predictions of laboratory-measured topsoil organic carbon beyond a non-satellite spatial baseline?*
- **FIN-Q1 — Economic value (later only):** *Do validated biogeochemical remote-sensing indicators add point-in-time information to economic forecasts after standard covariates and reporting lags?*

**Supervisor-facing preferred combined framing:** *How can a reproducible, API-first Earth-observation pipeline generate and validate uncertainty-aware indicators of environmental resource condition, with an optional biochemical comparison against independent field measurements?*

**Next evidence required to upgrade:** approval of thesis subquestion, legal source rights, labeled and temporally matched samples, independent performance comparison, accepted uncertainty analysis, reviewer sign-off, and strict public/private segregation.
