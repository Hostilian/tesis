# Chapter 2: Literature Review

<!-- AI-assisted rewording, 26 Nov 2026 (Claude). CZU Rector's Directive 7/2026, Art. 8(4) allows AI help with style, structure, rewording and source search in the literature review only. Declare this in the thesis declaration and the AI-use note. -->

This chapter covers the background the thesis builds on: how satellites measure the Earth's surface, how such measurements have been used as evidence of economic activity, how open satellite data is accessed, how change is detected and evaluated, and what earlier studies show about the Alentejo study region. It ends by stating the gap this thesis addresses.

## 2.1 How satellites measure the surface

Remote sensing means collecting information about the Earth's surface without touching it, by measuring the electromagnetic radiation that the surface reflects or emits [R201]. Textbooks describe two kinds of sensor: passive sensors, which record reflected sunlight or emitted heat, and active sensors, which send out their own signal and record the echo [R212, R214].

### 2.1.1 Optical sensors

Optical sensors record sunlight reflected in a set of wavelength bands. This thesis uses the MultiSpectral Instrument on Sentinel-2. It records 13 bands from visible light to short-wave infrared at 10, 20 or 60 m resolution, and with two satellites it revisits each place about every five days [R262]. Landsat 8, in orbit since 2013, records similar bands at 30 m [R238].

Different surfaces reflect light differently, and this is what makes the bands useful [R201]:

- **Vegetation** absorbs red light for photosynthesis and reflects strongly in the near infrared (NIR).
- **Bare soil** reflects more as the wavelength increases, with no sharp red–NIR contrast.
- **Water** absorbs almost all NIR and short-wave infrared (SWIR) light.

Spectral indices turn these differences into a single number per pixel. The Normalised Difference Vegetation Index (NDVI) compares red and NIR reflectance. It was introduced in the 1970s [R219] and became the standard measure of green vegetation [R215]. Related indices reduce the influence of soil brightness [R217] or highlight open water [R216]. The bare soil index used in this thesis follows the same logic, combining SWIR, red, NIR and blue.

The main limits of optical data are clouds, haze and illumination. Clouds hide the surface completely, and the atmosphere changes the signal even on clear days [R201]. Data providers therefore deliver "surface reflectance" products with an atmospheric correction and a per-pixel cloud and scene classification. Sentinel-2 Level-2A is such a product [R262].

### 2.1.2 Radar sensors

Synthetic Aperture Radar (SAR), for example on Sentinel-1, sends microwave pulses and measures the echo. Radar works through clouds and at night [R220, R221]. Smooth surfaces such as calm water look dark, vegetation scatters the signal in many directions, and buildings return strong echoes [R220]. Sentinel-1 time series have been used to detect deforestation under persistent cloud [R225]. This thesis does not use radar, but it is the obvious second source where clouds block optical images.

## 2.2 Satellite data as evidence of economic activity

Economists have used satellite data for about two decades. Donaldson and Storeygard review these uses and explain why they help: images cover places and periods that official statistics miss, at a fine spatial scale [R226].

**Night-time lights.** Light at night is related to population, economic activity and electricity use [R228]. Henderson, Storeygard and Weil used changes in night lights to improve estimates of GDP growth, especially for countries with weak statistics [R227]. Chen and Nordhaus reached a similar conclusion: lights add the most value where official data are poor, and little where statistics are good [R229]. Newer VIIRS night-light data are sharper than the older DMSP data and do not saturate in bright city centres [R230].

**Sector-level signals.** Optical images are used to detect and classify ships, which supports monitoring of shipping activity [R233]. Mining is directly visible from space: Maus and co-authors mapped mining areas worldwide from satellite images, which makes mining footprints comparable across countries [R235].

These studies treat the satellite signal as a proxy. A proxy can show that something changed. It cannot say why without other evidence. The thesis keeps this distinction in every result.

## 2.3 Open satellite data and how to access it

Three developments made satellite analysis possible without commercial licences or a data centre.

1. **Free data.** The EU Space Programme makes Copernicus data, including Sentinel-1 and Sentinel-2, free and open to everyone [R256]. Landsat data are also free [R238].
2. **Cloud platforms.** Google Earth Engine stores a multi-petabyte archive next to large-scale processing, so users run analyses without downloading data [R207]. The Copernicus Data Space Ecosystem has offered Sentinel data and processing services since 2023 [R202]. NASA Earthdata provides the US archives [R205].
3. **Standard catalogues.** The SpatioTemporal Asset Catalog (STAC) specification describes satellite scenes in a common JSON format, so one program can search several archives the same way [R250]. Combined with cloud-optimised image files, a script can read just the small window it needs from a scene.

The case study in this thesis uses the third route: a public STAC catalogue and windowed reads of public files, with no account and no platform lock-in.

## 2.4 Detecting change and anomalies

An anomaly is an observation that does not fit the expected pattern. A widely cited survey distinguishes three types [R239]:

- **point anomalies:** single unusual values;
- **contextual anomalies:** values that are unusual only in their place or season;
- **collective anomalies:** groups of values that together are unusual.

General-purpose detectors include the local outlier factor [R244], one-class support vector machines [R246] and Isolation Forest, which isolates unusual points with random splits [R206, R247].

For satellite images, the more specific field is change detection. Zhu reviews how Landsat time series are used to find change, and what affects the results: image frequency, preprocessing and the choice of algorithm [R240]. Two well-known approaches:

- LandTrendr fits trends to yearly images to find disturbance and recovery [R242].
- BFAST separates a time series into trend, seasonal and remaining parts, so that seasonal greening is not mistaken for change [R243].

The common lesson is that much apparent change is caused by season, weather, soil moisture or sensor differences. A method has to control for these before calling something a change.

The simplest method compares an index between two dates and flags pixels whose difference passes a threshold. It is easy to explain and to check. Its weak points are the choice of threshold and the dates. The thesis therefore fixes the threshold with a short-interval control pair and compares images from the same season.

## 2.5 Machine learning for Earth observation

Supervised classifiers such as random forests, support vector machines and neural networks are widely used to map land cover. Their quality depends on the quality and amount of training data [R245]. Unsupervised detectors need no labels, but they still need an interpretable input and an independent check [R247].

Foundation models pre-trained on large satellite archives, such as Prithvi, can be adapted to new tasks with fewer labels [R204, R248]. They require more computing power and are harder to explain.

This thesis has no independent field labels. It therefore uses a transparent index difference as its baseline and leaves trained models for future work.

## 2.6 Evaluating a change map without field data

Olofsson and co-authors set out good practice for checking land-change maps [R263]:

- sample the map with a defined design;
- compare it with reference data of higher quality than the map;
- report the error matrix and the uncertainty of the mapped area.

Where no field data exist, an independent map from a national agency can serve as the reference. Agreement with that map is then agreement with another map, not ground truth.

Two further issues matter for pixel data:

- **Neighbouring pixels are not independent**, so counting pixels overstates the evidence. Evaluating whole fields or polygons reduces this problem.
- **Mixed pixels.** At 10 m, a pixel in a hedgerow orchard mixes tree canopy, bare soil between rows and irrigation lines. Small features are therefore hard to resolve [R201].

## 2.7 Data engineering and web delivery

The pipeline follows the extract–transform–load (ETL) pattern described in the data-warehousing literature [R252]:

1. extract data from a source;
2. transform it into a clean, consistent form;
3. load it into a store that analysts use.

For geographic data, standards make each step reusable:

- The OGC Web Map Service defines how map images are requested [R249].
- GeoJSON is the standard JSON format for geographic features [R251]. Serving pre-computed results as GeoJSON lets a light web page show them without processing raster data itself.
- ISO 19115 defines what metadata should describe a dataset [R254].

Dashboards that turn such data into clear indicators are a form of decision support system. A survey of agricultural decision support shows the same needs found here: clear indicators, honest uncertainty and data the user can trust [R253].

## 2.8 Legal and ethical points

- **Licensing.** Copernicus data are free and open under the EU Space Programme [R256]. The Portuguese land-use map used as a reference is published under an open licence.
- **Privacy.** Data protection law applies when data can identify a person [R257]. At 10 m resolution, Sentinel-2 cannot show individuals. The thesis also avoids any private farm boundaries and uses public bounding boxes only.
- **Over-interpretation.** A change flag can affect how a farm or mine is seen. Results therefore always state what was measured and what is only interpretation.

## 2.9 The study region: irrigation and orchard expansion in Alentejo

The main case study lies in the area served by the Alqueva irrigation scheme in Alentejo, southern Portugal. Over the past 30 years, water from the Alqueva irrigation network let olive groves in Alentejo expand and intensify fast, mainly on the most productive soils [R265]. In one region of southern Portugal, irrigated olive groves went from almost none in 1990 to about 6 % of the area in 2017 [R264]. They replaced mainly open rainfed annual crops (63 % of the expansion) and traditional rainfed olive groves (21 %). Public irrigation water and large farms were the main drivers [R264].

Mapping these orchards from free satellite data works, but with limits:

- Around the Alqueva reservoir, a classifier using Sentinel-1 and Sentinel-2 images reached 91 % overall accuracy. It identified almond groves with an F1 score of 0.90 and three olive-growing systems with F1 scores of at least 0.78. Its agreement with the official map COS 2018 was lower (F1 score 0.60) [R266].
- Researchers at Portugal's Directorate-General for Territory (DGT) tested 2018 Sentinel-2 images over about 1.2 million ha of southern Portugal. Olive groves and orchards had the lowest producer's accuracy of all classes, 46 % and 35 %. The authors explain that a 10 m pixel mixes the trees with the soil around them [R269].
- A Sentinel-2 study of olive planting systems reached about 80 % accuracy. The most frequent errors were intensive or super-intensive groves labelled as traditional ones, and the authors name the 10 m pixel size as a challenge [R267].

The reference map in this thesis is COS, the land-use map of mainland Portugal made by DGT. Its 2018v4 and 2025v1 editions share one specification [R268]:

- polygons drawn by visual interpretation of very high resolution orthophotos, helped by administrative databases;
- a smallest mapped unit of 0.5 ha and 102 classes;
- a specified thematic accuracy of at least 85 %;
- separate classes for low-density, high-density and hedgerow olive groves and orchards.

DGT states that only these two editions can be compared with each other [R268].

## 2.10 Gap and position of this thesis

The literature offers the building blocks: free imagery, standard catalogues, well-studied indices, change-detection methods and good-practice evaluation. Studies usually report a method and a result. They rarely publish a complete, rerunnable path from catalogue entry to web map that records exactly which scenes, settings and code produced each number.

This thesis builds such a path for two public study areas in Portugal. It uses a deliberately simple and transparent change method, checks it against an official land-use map, and states what 10 m data can and cannot show.

## References cited in this chapter

<!-- Generated from thesis/latex/references.bib by thesis/tools/make_ch2_reflist.py. Do not edit by hand. -->

1. **Bouvet et al.** (2018). Use of the SAR Shadowing Effect for Deforestation Detection with Sentinel-1 Time Series. *Remote Sensing*, 10, 1250. https://doi.org/10.3390/rs10081250 [R225]
2. **Breunig et al.** (2000). LOF: identifying density-based local outliers. *Proceedings of the 2000 ACM SIGMOD International Conference on Management of Data*, 93–104. https://doi.org/10.1145/335191.335388 [R244]
3. **Butler et al.** (2016). The GeoJSON Format. *RFC 7946, Internet Engineering Task Force*. https://doi.org/10.17487/RFC7946 [R251]
4. **Campbell & Wynne** (2011). Introduction to Remote Sensing. *Guilford Press*. [R214]
5. **Chandola et al.** (2009). Anomaly detection: A survey. *ACM Computing Surveys*, 41, 1–58. https://doi.org/10.1145/1541880.1541882 [R239]
6. **Chen & Nordhaus** (2011). Using luminosity data as a proxy for economic statistics. *Proceedings of the National Academy of Sciences*, 108, 8589–8594. https://doi.org/10.1073/pnas.1017031108 [R229]
7. **Direção-Geral do Território** (2026). Especificações técnicas da Série 2 da Carta de Uso e Ocupação do Solo (COS) de Portugal Continental. https://geo2.dgterritorio.gov.pt/cos/ET/COS-Serie2-EspecificacoesTecnicas.pdf [R268]
8. **Donaldson & Storeygard** (2016). The View from Above: Applications of Satellite Data in Economics. *Journal of Economic Perspectives*, 30, 171–198. https://doi.org/10.1257/jep.30.4.171 [R226]
9. **Drusch et al.** (2012). Sentinel-2: ESA's Optical High-Resolution Mission for GMES Operational Services. *Remote Sensing of Environment*, 120, 25–36. https://doi.org/10.1016/j.rse.2011.11.026 [R262]
10. **Elvidge et al.** (1997). Relation between satellite observed visible-near infrared emissions, population, economic activity and electric power consumption. *International Journal of Remote Sensing*, 18, 1373–1379. https://doi.org/10.1080/014311697218485 [R228]
11. **Elvidge et al.** (2013). Why VIIRS data are superior to DMSP for mapping nighttime lights. *Proceedings of the Asia-Pacific Advanced Network*, 35, 62–69. https://doi.org/10.7125/APAN.35.7 [R230]
12. **European Parliament** (2021). Regulation (EU) 2021/696 of the European Space Programme. *Official Journal of the European Union*. [R256]
13. **European Parliament and Council of the European Union** (2016). Regulation (EU) 2016/679 on the protection of natural persons with regard to the processing of personal data and on the free movement of such data (General Data Protection Regulation). *Official Journal of the European Union, L 119, 4 May 2016, pp. 1–88*. https://eur-lex.europa.eu/eli/reg/2016/679/oj [R257]
14. **European Space Agency** (2023). Copernicus Data Space Ecosystem Portal. *https://dataspace.copernicus.eu/*. [R202]
15. **Gorelick et al.** (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment*, 202, 18–27. https://doi.org/10.1016/j.rse.2017.06.031 [R207]
16. **Henderson et al.** (2012). Measuring Economic Growth from Outer Space. *American Economic Review*, 102, 994–1028. https://doi.org/10.1257/aer.102.2.994 [R227]
17. **Hernandez et al.** (2020). Exploring Sentinel-2 for Land Cover and Crop Mapping in Portugal. *The International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences*, XLIII-B3-2020, 83–89. https://doi.org/10.5194/isprs-archives-XLIII-B3-2020-83-2020 [R269]
18. **Huete** (1988). A Soil-Adjusted Vegetation Index (SAVI). *Remote Sensing of Environment*, 25, 295–309. https://doi.org/10.1016/0034-4257(88)90106-X [R217]
19. **IBM & NASA** (2023). Prithvi-100M Geospatial Foundation Model. *Hugging Face Architecture*. [R204]
20. **ISO** (2014). ISO 19115-1:2014 Geographic Information – Metadata. *International Organization for Standardization*. https://www.iso.org/standard/53798.html [R254]
21. **Jakubik et al.** (2023). Foundation Models for Generalist Geospatial Artificial Intelligence. *arXiv preprint arXiv:2310.18660*. https://arxiv.org/abs/2310.18660 [R248]
22. **Jensen** (2015). Introductory Digital Image Processing: A Remote Sensing Perspective. *Pearson*. [R212]
23. **Kanjir et al.** (2018). Vessel detection and classification from spaceborne optical images: A literature survey. *Remote Sensing of Environment*, 207, 1–26. https://doi.org/10.1016/j.rse.2017.12.033 [R233]
24. **Kennedy et al.** (2010). Detecting trends in forest disturbance and recovery using yearly Landsat time series: 1. LandTrendr – Temporal segmentation algorithms. *Remote Sensing of Environment*, 114, 2897–2910. https://doi.org/10.1016/j.rse.2010.07.008 [R242]
25. **Lillesand et al.** (2015). Remote Sensing and Image Interpretation. *John Wiley & Sons*. [R201]
26. **Liu et al.** (2008). Isolation Forest. *2008 Eighth IEEE International Conference on Data Mining*, 413–422. https://doi.org/10.1109/ICDM.2008.17 [R206]
27. **Liu et al.** (2012). Isolation-based anomaly detection. *ACM Transactions on Knowledge Discovery from Data*, 6, 3. https://doi.org/10.1145/2133360.2133363 [R247]
28. **Martínez-Ruedas et al.** (2025). Assessment of CNN-based methods for discrimination of olive planting systems with Sentinel-2 images. *Computers and Electronics in Agriculture*, 234, 110311. https://doi.org/10.1016/j.compag.2025.110311 [R267]
29. **Maus et al.** (2020). A global-scale data set of mining areas. *Scientific Data*, 7, 289. https://doi.org/10.1038/s41597-020-00624-w [R235]
30. **Maxwell et al.** (2018). Implementation of machine-learning classification in remote sensing: an applied review. *International Journal of Remote Sensing*, 39, 2784–2817. https://doi.org/10.1080/01431161.2018.1433343 [R245]
31. **McFeeters** (1996). The use of the Normalized Difference Water Index (NDWI) in lake water mapping. *International Journal of Remote Sensing*, 17, 1425–1432. https://doi.org/10.1080/01431169608948714 [R216]
32. **Moreira & others** (2013). A tutorial on synthetic aperture radar. *IEEE Geoscience and Remote Sensing Magazine*, 1, 6–43. https://doi.org/10.1109/MGRS.2013.2248301 [R221]
33. **Morgado et al.** (2022). Drivers of irrigated olive grove expansion in Mediterranean landscapes and associated biodiversity impacts. *Landscape and Urban Planning*, 225, 104429. https://doi.org/10.1016/j.landurbplan.2022.104429 [R264]
34. **Muñoz-Rojas et al.** (2024). Pedoclimatic and Landscape Conditions of Olive Groves in Portugal and Alentejo. *The Olive Landscapes of the Mediterranean*, 36, 291–301. https://doi.org/10.1007/978-3-031-57956-1_28 [R265]
35. **NASA Earthdata** (2024). NASA Earthdata Search Portal. *https://earthdata.nasa.gov/*. [R205]
36. **Olofsson et al.** (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sensing of Environment*, 148, 42–57. https://doi.org/10.1016/j.rse.2014.02.015 [R263]
37. **Open Geospatial Consortium** (2006). OpenGIS Web Map Server Implementation Specification, version 1.3.0. *OGC document 06-042*. https://www.ogc.org/standard/wms/ [R249]
38. **Quintela et al.** (2025). Refining European Crop Mapping Classification Through the Integration of Permanent Crops: A Case Study in Rapidly Transitioning Irrigated Landscapes Induced by Dam Construction. *Remote Sensing*, 17, 3979. https://doi.org/10.3390/rs17243979 [R266]
39. **Rouse et al.** (1974). Monitoring vegetation systems in the Great Plains with ERTS. [R219]
40. **Roy et al.** (2014). Landsat-8: Science and product vision for terrestrial global change research. *Remote Sensing of Environment*, 145, 154–172. https://doi.org/10.1016/j.rse.2014.02.001 [R238]
41. **Scholkopf et al.** (2001). Estimating the support of a high-dimensional distribution. *Neural Computation*, 13, 1443–1471. https://doi.org/10.1162/089976601750264965 [R246]
42. **STAC Spec Group** (2023). SpatioTemporal Asset Catalog API specification version 1.0.0. *STAC Catalog GitHub*. https://stacspec.org [R250]
43. **Tucker** (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment*, 8, 127–150. https://doi.org/10.1016/0034-4257(79)90013-0 [R215]
44. **Vassiliadis** (2009). A Survey of Extract–Transform–Load Technology. *International Journal of Data Warehousing and Mining*, 5, 1–27. https://doi.org/10.4018/jdwm.2009070101 [R252]
45. **Verbesselt et al.** (2010). Detecting trend and seasonal changes in satellite image time series. *Remote Sensing of Environment*, 114, 106–115. https://doi.org/10.1016/j.rse.2009.08.014 [R243]
46. **Woodhouse** (2006). Introduction to Microwave Remote Sensing. *CRC Press*. [R220]
47. **Zhai et al.** (2020). Decision support systems for agriculture 4.0: Survey and challenges. *Computers and Electronics in Agriculture*, 170, 105256. https://doi.org/10.1016/j.compag.2020.105256 [R253]
48. **Zhu** (2017). Change detection using Landsat time series: A review of frequencies, preprocessing, algorithms, and applications. *ISPRS Journal of Photogrammetry and Remote Sensing*, 130, 370–384. https://doi.org/10.1016/j.isprsjprs.2017.06.013 [R240]
