// =============================================================
// APEX CAPITAL PARTNERS - SPACE-BASED ARBITRAGE CONTROLLER V4
// =============================================================

// Global state variables
let map, radarChartInstance;
let anomaliesData = [];
let regionsData = null;
let currentSelectedAnomaly = null;

let currentLang = localStorage.getItem("orbital_lang") || 'EN';
if (!['EN', 'CS', 'ES'].includes(currentLang)) {
    currentLang = 'EN';
}
let translations = { EN: null, CS: null, ES: null };

// Advanced GIS & WebGL state
let darkBasemapLayer, satelliteBasemapLayer;
let heatmapLayer = null;
let heatmapActive = false;
let mapMarkers = []; 
let currentBandMode = 'rgb'; 

// Three.js 3D Globe state
let globeScene, globeCamera, globeRenderer, globeMesh, orbitLinesGroup;

// Academic Chapters Content Cache (CZU Prague Bachelor Thesis by Eren Ozturk)
const academicChapters = {
    "1": {
        title: "Chapter 1: Introduction",
        sections: [
            { name: "1.1 Background & Motivation", text: "In the modern digital economy, information engineering has expanded beyond terrestrial borders. The rise of Earth Observation (EO) satellite constellations, coupled with cloud-based geospatial computing platforms, has birthed a new domain: Space-Based Economic Intelligence. Remote sensing offers continuous, independent, and spatially explicit alternatives to legacy statistical indicators." },
            { name: "1.2 Problem Statement", text: "Translating raw, noisy, multi-spectral raster feeds into structured, actionable economic intelligence remains a critical engineering gap. Traditional geospatial analysis relies on localized human photo-interpretation which fails to scale to national or continental monitoring." },
            { name: "1.3 Research Questions", text: "RQ1: How reliably can open satellite spectral APIs identify localized industrial and mining resource anomalies compared to ground truth records?<br>RQ2: What is the correlation between VIIRS night-time light fluctuations and macro/microeconomic indicators in the target regions?<br>RQ3: What pipeline latency and processing constraints limit the scalability of free satellite APIs for real-time economic monitoring?" }
        ]
    },
    "2": {
        title: "Chapter 2: Theoretical Framework & Literature Review",
        sections: [
            { name: "2.1 Remote Sensing Principles", text: "Remote sensing measures electromagnetic radiation reflected or emitted from sensors. Modalities include passive sensors (Sentinel-2, Landsat) capturing reflected solar bands, and active sensors (Sentinel-1 SAR) emitting radar beams that penetrate cloud cover." },
            { name: "2.2 Economic Indicators", text: "Mining footprints, shipping volume indexes, and urban night lights radiance (VIIRS DNB) act as leading economic proxies. Unsupervised anomaly models like Isolation Forest isolate outliers without requiring extensive labelled ground-truth grids." }
        ]
    },
    "3": {
        title: "Chapter 3: Methodology",
        sections: [
            { name: "3.1 Multi-Spectral Index Formulations", text: "To detect physical changes, raw spectral bands are combined mathematically:<br><strong>NDVI</strong> = (NIR - Red) / (NIR + Red) - measures forest density.<br><strong>NDWI</strong> = (Green - NIR) / (Green + NIR) - measures open water surface.<br><strong>BSI</strong> = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue)) - isolates exposed mining soil." },
            { name: "3.2 Unsupervised AI Engine", text: "A multi-spectral feature matrix is extracted and fed into an Isolation Forest model (contamination = 0.08) to calculate path length distributions, effectively isolating anomalous land cover deviations." }
        ]
    },
    "4": {
        title: "Chapter 4: System Design & Implementation",
        sections: [
            { name: "4.1 Decoupled GIS Architecture", text: "A high-performance Python data engineering back-end handles raster processing and model fitting. A lightweight flat JSON serialization layer acts as a cache. An interactive WebGL/HTML5 frontend renders maps, sliders, and radar charts." },
            { name: "4.2 Credential Protection", text: "Google Earth Engine initialization relies on GCP Project ID isolation, securing credentials in backend environment variables and Colab UserData, keeping the production deployment serverless and secure." },
            { name: "4.5.4 Multi-Version Dashboard", text: "Implements three visual editions: V2 (Academic Baseline), V3 (Sci-Fi Cyber HUD with 3D Globe), and V4 (Institutional YC Investor & Portfolio Telemetry Console with interactive pipeline diagrams, Vanguard Screener with $50M CRO limit alert, and compliance JSON exporter)." }
        ]
    },
    "5": {
        title: "Chapter 5: Results & Analysis",
        sections: [
            { name: "5.1 Case Study Highlights", text: "Salar de Atacama (Chile) showed lithium evaporation pond extensions (NDWI surge to 0.58). Madre de Dios (Peru) flagged illegal mining clearings (NDVI drop to -0.52). Czechia industrial nodes showed quarterly GDP correlation (r = 0.724)." },
            { name: "5.2 Hypothesis Validation", text: "Hypothesis H1 (F1-score > 0.80) was validated with F1 = 0.907. Hypothesis H2 (NTL radiance correlation r >= 0.65) was validated with r = 0.724 (p = 0.0002)." }
        ]
    },
    "6": {
        title: "Chapter 6: Discussion & Conclusion",
        sections: [
            { name: "6.1 Research Contributions", text: "This thesis demonstrates that open-access satellite APIs, in conjunction with unsupervised Isolation Forests, can detect hidden mining and industrial anomalies with high accuracy, establishing a framework for real-time supply chain auditing." },
            { name: "6.2 Study Limitations", text: "Primary constraints include cloud obstruction in optical channels and spatial resolutions (10m) missing micro-scale operations, which can be mitigated in future work via Sentinel-1 SAR and atmospheric sensor fusion." },
            { name: "6.9 Portfolio & VC Applications", text: "Demonstrates immediate translational value of satellite telemetry for hedge funds and venture capital, bridging Earth observation indices with portfolio allocation rules, CRO risk ceilings ($50M cap), and standardized compliance JSON output." }
        ]
    },
    "7": {
        title: "Chapter 7: Summary",
        sections: [
            { name: "7.1 Summary of Contributions", text: "We have built an end-to-end reproducible economic pipeline joining GEE, CDSE, and World Bank indicators. Anomaly models are fully integrated and verified via unit tests and automated github page deployments." }
        ]
    }
};

const academicChaptersCS = {
    "1": {
        title: "Kapitola 1: Úvod",
        sections: [
            { name: "1.1 Kontext a motivace", text: "V moderní digitální ekonomice se informační inženýrství rozšířilo za terestriální hranice. Vznik satelitních konstelací pro pozorování Země (EO) ve spojení s cloudovými platformami dal vzniknout novému oboru: Vesmírné ekonomické inteligenci." },
            { name: "1.2 Formulace problému", text: "Navzdory dostatku otevřených satelitních dat přetrvává kritická mezera: jak převést surové multi-spektrální rastrové snímky do strukturovaných ekonomických anomálií." },
            { name: "1.3 Výzkumné otázky", text: "RQ1: Jak spolehlivě dokážou otevřená satelitní API identifikovat lokalizované anomálie těžby surovin ve srovnání s úředními registry?<br>RQ2: Jaká je korelace mezi kolísáním nočního osvětlení VIIRS a makro/mikroekonomickými ukazateli?<br>RQ3: Jaká výkonnostní omezení limitují škálovatelnost bezplatných satelitních API?" }
        ]
    },
    "2": {
        title: "Kapitola 2: Teoretický rámec",
        sections: [
            { name: "2.1 Principy dálkového průzkumu Země", text: "Dálkový průzkum je věda o získávání informací o zemském povrchu bez fyzického kontaktu, a to měřením elektromagnetického záření. Mezi hlavní platformy patří optické (Sentinel-2, Landsat) a radarové (Sentinel-1 SAR) senzory." }
        ]
    },
    "3": {
        title: "Kapitola 3: Metodika",
        sections: [
            { name: "3.1 Multi-spektrální indexy", text: "K detekci změn jsou využívány matematické kombinace pásem:<br><strong>NDVI</strong> (vegetace), <strong>NDWI</strong> (vodní plochy), <strong>BSI</strong> (odhalená půda)." }
        ]
    },
    "4": {
        title: "Kapitola 4: Návrh systému",
        sections: [
            { name: "4.1 Architektura GIS", text: "Systém je navržen jako modulární zpracovatelská pipeline v jazyce Python s ukládáním výsledků do plochých JSON souborů, což eliminuje únik přístupových klíčů na klientské straně." },
            { name: "4.5.4 Víceverzový Dashboard", text: "Implementuje tři verze uživatelského rozhraní: V2 (akademická verze), V3 (hud s 3D glóbusem) a V4 (institucionální rozhraní s investičními filtry a limity)." }
        ]
    },
    "5": {
        title: "Kapitola 5: Výsledky",
        sections: [
            { name: "5.1 Případové studie", text: "Salar de Atacama (Chile) vykázala expanzi odpařovacích nádrží na lithium (nárůst NDWI). Madre de Dios (Peru) detekovala nelegální těžbu zlata (pokles NDVI). Mladá Boleslav (ČR) prokázala korelaci nočního osvětlení s HDP (r = 0.724)." }
        ]
    },
    "6": {
        title: "Kapitola 6: Diskuze",
        sections: [
            { name: "6.1 Přínosy a limity", text: "Práce prokazuje využitelnost bezplatných API pro ekonomické předpovědi a audit dodavatelských řetězců. Hlavním limitem zůstává oblačnost a prostorové rozlišení (10m)." },
            { name: "6.9 Portfoliové aplikace a VC", text: "Dokazuje přímý přínos satelitní telemetrie pro rizikový kapitál a zajišťovací fondy, propojení detekce anomálií s alokačními pravidly Vanguard a CRO limitem $50 mil." }
        ]
    },
    "7": {
        title: "Kapitola 7: Závěr",
        sections: [
            { name: "7.1 Souhrn přínosů", text: "Byl vytvořen plně reprodukovatelný model pro detekci ekonomických anomálií ze satelitních dat s interaktivním dashboardem nasazeným na GitHub Pages." }
        ]
    }
};

const academicChaptersES = {
    "1": {
        title: "Capítulo 1: Introducción",
        sections: [
            { name: "1.1 Contexto y Motivación", text: "En la economía digital moderna, la ingeniería de la información se ha expandido más allá de las fronteras terrestres. El surgimiento de las constelaciones de satélites de Observación de la Tierra (EO), junto con las plataformas de computación geoespacial en la nube, ha dado origen a un nuevo dominio: la Inteligencia Económica Basada en el Espacio. La teledetección ofrece alternativas continuas, independientes y espacialmente explícitas a los indicadores estadísticos tradicionales." },
            { name: "1.2 Planteamiento del Problema", text: "Traducir transmisiones de trama multiespectrales ruidosas y sin procesar en anomalías de inteligencia económica estructuradas y accionables sigue siendo una brecha de ingeniería crítica. El análisis geoespacial tradicional depende de la fotointerpretación humana localizada, que no escala para el monitoreo nacional o continental." },
            { name: "1.3 Preguntas de Investigación", text: "PI1: ¿Con qué fiabilidad pueden las API espectrales abiertas de satélites identificar anomalías localizadas en recursos industriales y mineros en comparación con los registros reales en tierra?<br>PI2: ¿Cuál es la correlación entre las fluctuaciones de luz nocturna de VIIRS y los indicadores macro/microeconómicos en las regiones objetivo?<br>PI3: ¿Qué limitaciones de latencia del flujo de procesamiento restringen la escalabilidad de las API gratuitas de satélites para el monitoreo económico en tiempo real?" }
        ]
    },
    "2": {
        title: "Capítulo 2: Marco Teórico y Revisión de Literatura",
        sections: [
            { name: "2.1 Principios de Teledetección", text: "La teledetección mide la radiación electromagnética reflejada o emitida por sensores. Las modalidades incluyen sensores pasivos (Sentinel-2, Landsat) que capturan bandas solares reflejadas, y sensores activos (Sentinel-1 SAR) que emiten haces de radar que penetran la cobertura de nubes." },
            { name: "2.2 Indicadores Económicos", text: "La huella minera, los índices de volumen de transporte y la radiancia de luces nocturnas urbanas (VIIRS DNB) actúan como indicadores económicos clave. Los modelos de anomalías no supervisados, como Isolation Forest, aíslan los valores atípicos sin requerir redes extensas etiquetadas de control en tierra." }
        ]
    },
    "3": {
        title: "Capítulo 3: Metodología",
        sections: [
            { name: "3.1 Formulaciones de Índices Multiespectrales", text: "Para detectar cambios físicos, las bandas espectrales sin procesar se combinan matemáticamente:<br><strong>NDVI</strong> = (NIR - Rojo) / (NIR + Rojo) - mide la densidad forestal.<br><strong>NDWI</strong> = (Verde - NIR) / (Verde + NIR) - mide la superficie de agua abierta.<br><strong>BSI</strong> = ((SWIR1 + Rojo) - (NIR + Azul)) / ((SWIR1 + Rojo) + (NIR + Azul)) - aísla el suelo minero expuesto." },
            { name: "3.2 Motor de Inteligencia Artificial No Supervisado", text: "Se extrae una matriz de características multiespectrales y se alimenta a un modelo de Isolation Forest (tasa de contaminación = 0.08) para calcular las distribuciones de longitud de ruta, aislando las desviaciones anómalas de la cobertura del suelo." }
        ]
    },
    "4": {
        title: "Capítulo 4: Diseño del Sistema e Implementación",
        sections: [
            { name: "4.1 Arquitectura GIS Desacoplada", text: "Un extremo de ingeniería de datos en Python de alto rendimiento gestiona el procesamiento de tramas y el ajuste de modelos. Una capa de serialización JSON plana y ligera actúa como caché. Una interfaz interactiva WebGL/HTML5 renderiza mapas, deslizadores y gráficos de radar." },
            { name: "4.2 Protección de Credenciales", text: "La inicialización de Google Earth Engine se basa en el aislamiento de ID de proyecto GCP, asegurando las credenciales en variables de entorno del backend y Colab UserData, manteniendo el despliegue de producción seguro y sin servidor." },
            { name: "4.5.4 Dashboard Multiversión", text: "Implementa tres versiones de interfaz: V2 (akademická verze), V3 (hud con globo 3D) y V4 (consola de telemetría de cartera e inversiones YC con diagramas interactivos, examinador Vanguard con alerta de límite de riesgo CRO de $50M y exportador de cumplimiento JSON)." }
        ]
    },
    "5": {
        title: "Capítulo 5: Resultados y Análisis",
        sections: [
            { name: "5.1 Aspectos Destacados de los Casos de Estudio", text: "El Salar de Atacama (Chile) mostró extensiones de estanques de evaporación de litio (aumento de NDWI a 0.58). Madre de Dios (Perú) detectó claros de minería ilegal (caída de NDVI a -0.52). Los nodos industriales en Chequia mostraron una correlación trimestral del PIB (r = 0.724)." },
            { name: "5.2 Validación de Hipótesis", text: "La hipótesis H1 (puntuación F1 > 0.80) se validó con un F1 = 0.907. La hipótesis H2 (correlación de radiancia NTL r >= 0.65) se validó con r = 0.724 (p = 0.0002)." }
        ]
    },
    "6": {
        title: "Capítulo 6: Discusión y Conclusiones",
        sections: [
            { name: "6.1 Contribuciones de la Investigación", text: "Esta tesis demuestra que las API abiertas de satélites, junto con Isolation Forests no supervisados, pueden detectar anomalías mineras e industriales ocultas con alta precisión, estableciendo un marco de trabajo para la auditoría de cadenas de suministro en tiempo real." },
            { name: "6.2 Limitaciones del Estudio", text: "Las restricciones principales incluyen la obstrucción por nubes en canales ópticos y resoluciones espaciales (10m) que omiten operaciones a microescala, las cuales pueden mitigarse en trabajos futuros mediante Sentinel-1 SAR y fusión de sensores atmosféricos." },
            { name: "6.9 Aplicaciones de Cartera y Capital de Riesgo", text: "Demuestra el valor de traducción de la telemetría satelital para fondos de cobertura y capital de riesgo, vinculando índices de observación de la Tierra con reglas de asignación de cartera, límites de riesgo CRO ($50M) y exportaciones estructuradas de cumplimiento JSON." }
        ]
    },
    "7": {
        title: "Capítulo 7: Resumen",
        sections: [
            { name: "7.1 Resumen de Contribuciones", text: "Hemos desarrollado una canalización económica reproducible de extremo a extremo que conecta GEE, CDSE e indicadores del Banco Mundial. Los modelos de anomalías están completamente integrados y verificados a través de pruebas unitarias y despliegues automáticos en páginas de github." }
        ]
    }
};

// Vanguard Fund Screener Database
const vanguardFunds = [
    {
        ticker: "VOO",
        name: "Vanguard S&P 500 ETF",
        vehicle: "ETF",
        category: "Large Cap Blend",
        expense_ratio: 0.03,
        r1y: 24.12,
        r3y: 8.54,
        r5y: 14.22,
        r10y: 12.85,
        sharpe: 0.72,
        beta: 1.00,
        aum: 1140.50,
        history: 15,
        lipper: 92,
        recommendation: "OVERWEIGHT",
        rationale: "Vanguard S&P 500 ETF (VOO) exhibits top-tier cost efficiency with a 0.03% expense ratio. Risk metrics fall perfectly within expected benchmark limits. Track record exceeds minimum Discipline principles.",
        risk_flags: [],
        weight: 0.30
    },
    {
        ticker: "VGT",
        name: "Vanguard Information Tech ETF",
        vehicle: "ETF",
        category: "Technology",
        expense_ratio: 0.10,
        r1y: 31.50,
        r3y: 12.40,
        r5y: 18.90,
        r10y: 20.15,
        sharpe: 0.91,
        beta: 1.25,
        aum: 68.40,
        history: 22,
        lipper: 98,
        recommendation: "OVERWEIGHT",
        rationale: "Vanguard Information Technology ETF (VGT) delivers exceptional risk-adjusted alpha. The expense ratio is well below the 0.20% ceiling, and the fund represents a core sector overlay.",
        risk_flags: [],
        weight: 0.25
    },
    {
        ticker: "VTI",
        name: "Vanguard Total Stock Market ETF",
        vehicle: "ETF",
        category: "Large Cap Blend",
        expense_ratio: 0.03,
        r1y: 23.85,
        r3y: 8.12,
        r5y: 13.75,
        r10y: 12.20,
        sharpe: 0.69,
        beta: 1.01,
        aum: 1605.20,
        history: 25,
        lipper: 89,
        recommendation: "NEUTRAL",
        rationale: "Vanguard Total Stock Market ETF (VTI) offers maximum diversification at low cost (0.03%). However, for a Long/Short mandate, specific sector overlays (like VGT) are preferred over broad beta.",
        risk_flags: [],
        weight: 0.20
    },
    {
        ticker: "BND",
        name: "Vanguard Total Bond Market ETF",
        vehicle: "ETF",
        category: "Intermediate Core Bond",
        expense_ratio: 0.03,
        r1y: 4.10,
        r3y: -2.15,
        r5y: 0.45,
        r10y: 1.35,
        sharpe: -0.15,
        beta: 0.05,
        aum: 312.80,
        history: 19,
        lipper: 64,
        recommendation: "UNDERWEIGHT",
        rationale: "BND is outside Apex Capital's primary Long/Short Equity strategy. Moderate yield curve positioning. Keep as minimal liquidity ballast only.",
        risk_flags: ["STRATEGY_MISMATCH"],
        weight: 0.10
    },
    {
        ticker: "VMFXX",
        name: "Vanguard Federal Money Market",
        vehicle: "Money Market",
        category: "Money Market",
        expense_ratio: 0.11,
        r1y: 5.25,
        r3y: 3.80,
        r5y: 2.40,
        r10y: 1.60,
        sharpe: 2.10,
        beta: 0.00,
        aum: 285.40,
        history: 45,
        lipper: 85,
        recommendation: "NEUTRAL",
        rationale: "VMFXX is highly liquid and safe, yielding standard yield curve rates. Used for cash management optimization but not for capital growth. APY remains stable.",
        risk_flags: ["STRATEGY_MISMATCH"],
        weight: 0.15
    },
    {
        ticker: "VINF",
        name: "Vanguard Inception Frontier Fund",
        vehicle: "Mutual Fund",
        category: "Emerging Markets",
        expense_ratio: 0.28,
        r1y: 18.20,
        r3y: null,
        r5y: null,
        r10y: null,
        sharpe: null,
        beta: 1.40,
        aum: 0.80,
        history: 1.5,
        lipper: null,
        recommendation: "AVOID",
        rationale: "Vanguard Inception Frontier Fund (VINF) is flagged on two core parameters. The expense ratio (0.28%) exceeds our 0.20% ceiling, and its track record of 1.5 years fails the 3-year Discipline rule.",
        risk_flags: ["HIGH_EXPENSE_RATIO", "INSUFFICIENT_HISTORY"],
        weight: 0.05
    }
];

let selectedFundTicker = "VOO";

// Satellite Telemetry Messages
const telemetryMessages = [
    "📡 ACP-1 (SENTINEL-2): Multi-spectral scan at Salar de Atacama [Lithium] completed...",
    "📡 ACP-2 (LANDSAT-9): Logistics density scan in Madre de Dios [Gold] completed...",
    "📡 ACP-3 (VIIRS): Czechia industrial night lights radiance anomaly Z-score at +3.84...",
    "📡 ACP-1 (SENTINEL-1): SAR radar imagery penetrating cloud cover in Atacama basin...",
    "📡 ACP-2 (LANDSAT-8): Automated crop-masking anomaly pipeline resolved for Czechia node..."
];
let telemetryIndex = 0;

// Pipeline Node Specifications
const pipelineNodes = {
    "node-raw": {
        name: "Orbital Satellite Sensors",
        desc: "Raw, multi-spectral and radar raster data acquired from Sentinel-2 (Copernicus CDSE), Landsat-8/9 (USGS), and Suomi-NPP VIIRS (NASA). Refreshed at revisit cycles between 5 to 12 days.",
        meta: [
            "• constellations: Sentinel-1/2, Landsat-8/9, Suomi-NPP",
            "• spatial_resolution: 10m Optical, 20m SAR",
            "• raw_bands: B2, B3, B4, B8, B11, B12"
        ],
        status: "ACTIVE"
    },
    "node-ingestion": {
        name: "Copernicus CDSE API Ingestor",
        desc: "Automated ingestion pipeline query using public APIs. Downloads spatial tiles, performs cloud-masking algorithms, and computes mathematical multi-spectral indices (NDVI, NDWI, BSI).",
        meta: [
            "• api_target: Copernicus CDSE REST API",
            "• latency: ~245ms average request latency",
            "• pipeline_format: Cloud-Optimized GeoTIFF (COG)"
        ],
        status: "ACTIVE"
    },
    "node-ai": {
        name: "Isolation Forest ML Engine",
        desc: "Unsupervised machine learning model trained on regional multi-spectral feature matrices. Calculates path length distributions to isolate anomalous soil, water, and night radiance deviations.",
        meta: [
            "• algorithm: Unsupervised Isolation Forest",
            "• parameters: estimators=100, contamination=0.08",
            "• anomaly_threshold: Z-Score > 2.50 (|Z|)"
        ],
        status: "ACTIVE"
    },
    "node-allocator": {
        name: "Apex Capital Portfolio Allocator",
        desc: "Translates high-confidence anomalies into asset overlay signals. Maps regional extraction increases or supply chain disruptions directly to primary holding tickers (e.g., SQM, ALB, FCX).",
        meta: [
            "• strategy: Long/Short Equity Overlay",
            "• position_sizing: Dynamic rebalancing weight",
            "• risk_limits: CRO limit checking ($50M cap)"
        ],
        status: "ACTIVE"
    }
};

// Map CartoDB Dark basemap tiles
const darkMatterTilesUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const mapAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialise UI Languages
    try { updateUILanguage(); } catch (e) { console.error("Error updating initial language:", e); }
    try { loadDashboardData(); } catch (e) { console.error("Error loading dashboard data:", e); }

    // 2. Initialize UI components inside try-catch isolation blocks
    try { initStarsBackground(); } catch (e) { console.error("initStarsBackground failed:", e); }
    try { initMap(); } catch (e) { console.error("initMap failed:", e); }
    try { initMinimap(); } catch (e) { console.error("initMinimap failed:", e); }
    try { initRadarChart(); } catch (e) { console.error("initRadarChart failed:", e); }
    try { init3DGlobe(); } catch (e) { console.error("init3DGlobe failed:", e); }
    try { initScreenerTable(); } catch (e) { console.error("initScreenerTable failed:", e); }
    try { initPipelineInteractivity(); } catch (e) { console.error("initPipelineInteractivity failed:", e); }
    try { setupEventListeners(); } catch (e) { console.error("setupEventListeners failed:", e); }
    
    // 3. Cycle Telemetry feed
    setInterval(() => {
        const feed = document.getElementById("satellite-telemetry-feed");
        if (feed) {
            telemetryIndex = (telemetryIndex + 1) % telemetryMessages.length;
            feed.innerHTML = telemetryMessages[telemetryIndex];
        }
    }, 4500);

    // 4. Run live API connection status checks
    try { checkLiveAPIHealth(); } catch(e) { console.error("checkLiveAPIHealth failed:", e); }
});

// 1. STARFIELD PARALLAX WARP SYSTEM & DRIFTING APEX SATELLITES
function initStarsBackground() {
    const canvas = document.getElementById("stars-canvas");
    const ctx = canvas.getContext("2d");
    
    let stars = [];
    const count = 100;
    
    let warpCenter = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    let targetWarpCenter = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    
    window.addEventListener("mousemove", (e) => {
        targetWarpCenter.x = e.clientX;
        targetWarpCenter.y = e.clientY;
    });
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        targetWarpCenter.x = canvas.width / 2;
        targetWarpCenter.y = canvas.height / 2;
    }
    window.addEventListener("resize", resize);
    resize();
    
    // Initialize warp stars
    for (let i = 0; i < count; i++) {
        stars.push({
            angle: Math.random() * Math.PI * 2,
            dist: Math.random() * (canvas.width / 2),
            speed: Math.random() * 0.5 + 0.1,
            size: Math.random() * 1.2 + 0.4
        });
    }

    // Drifting Satellites
    let bgSatellites = [];
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        warpCenter.x += (targetWarpCenter.x - warpCenter.x) * 0.04;
        warpCenter.y += (targetWarpCenter.y - warpCenter.y) * 0.04;
        
        stars.forEach(s => {
            s.dist += s.speed;
            
            if (s.dist > Math.max(canvas.width, canvas.height) * 0.8) {
                s.dist = Math.random() * 20;
                s.angle = Math.random() * Math.PI * 2;
                s.speed = Math.random() * 0.5 + 0.1;
            }
            
            const x = warpCenter.x + Math.cos(s.angle) * s.dist;
            const y = warpCenter.y + Math.sin(s.angle) * s.dist;
            
            const alpha = Math.min(1, s.dist / 200) * 0.25;
            ctx.strokeStyle = `rgba(212, 175, 55, ${alpha})`;
            ctx.lineWidth = s.size;
            
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x - Math.cos(s.angle) * (s.size * 4), y - Math.sin(s.angle) * (s.size * 4));
            ctx.stroke();
        });

        // Spawn drifting satellites (V4 Gold Edition)
        if (Math.random() < 0.0006 && bgSatellites.length < 2) {
            bgSatellites.push({
                x: -60,
                y: Math.random() * (canvas.height * 0.6) + canvas.height * 0.1,
                speed: Math.random() * 0.4 + 0.2,
                pulseTimer: 0
            });
        }

        bgSatellites.forEach((sat, idx) => {
            sat.x += sat.speed;
            sat.y += Math.sin(sat.x * 0.015) * 0.15;
            sat.pulseTimer++;

            if (sat.x > canvas.width + 60) {
                bgSatellites.splice(idx, 1);
                return;
            }

            ctx.save();
            ctx.translate(sat.x, sat.y);
            
            // Solar Panels
            ctx.fillStyle = "rgba(16, 185, 129, 0.4)"; // Return Emerald green panel
            ctx.strokeStyle = "rgba(212, 175, 55, 0.5)";  // Gold trim
            ctx.lineWidth = 0.5;
            ctx.fillRect(-10, -2, 5, 4);
            ctx.strokeRect(-10, -2, 5, 4);
            ctx.fillRect(5, -2, 5, 4);
            ctx.strokeRect(5, -2, 5, 4);

            // Connector
            ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
            ctx.beginPath();
            ctx.moveTo(-5, 0); ctx.lineTo(5, 0);
            ctx.stroke();

            // Main body
            ctx.fillStyle = "rgba(212, 175, 55, 0.8)"; // Gold body
            ctx.fillRect(-2.5, -2.5, 5, 5);
            ctx.strokeRect(-2.5, -2.5, 5, 5);

            // Telemetry Light
            const blink = Math.floor(sat.pulseTimer / 25) % 2 === 0;
            ctx.fillStyle = blink ? "#00f59b" : "#ef4444";
            ctx.beginPath();
            ctx.arc(0, 0, 1.0, 0, Math.PI * 2);
            ctx.fill();

            ctx.restore();
        });
        
        requestAnimationFrame(animate);
    }
    animate();
}

// 2. THREE.JS 3D EARTH GLOBE SYSTEM (GOLD INSTITUTIONAL EDITION)
function init3DGlobe() {
    const container = document.getElementById("globe-container");
    if (!container) return;
    
    const fallback = document.getElementById("globe-fallback");
    const width = container.clientWidth || 320;
    const height = container.clientHeight || 320;
    
    try {
        globeScene = new THREE.Scene();
        globeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        globeCamera.position.z = 180;
        
        globeRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    } catch (e) {
        console.warn("WebGL not supported in this client:", e);
        if (fallback) fallback.style.display = "flex";
        return;
    }
    
    if (fallback) fallback.style.display = "none";
    globeRenderer.setSize(width, height);
    globeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(globeRenderer.domElement);
    
    // Wireframe Earth (Gold wireframe for V4)
    const geometry = new THREE.SphereGeometry(50, 18, 18);
    const material = new THREE.MeshBasicMaterial({
        color: 0xd4af37,
        wireframe: true,
        transparent: true,
        opacity: 0.18
    });
    
    globeMesh = new THREE.Mesh(geometry, material);
    globeScene.add(globeMesh);
    
    // Dark core
    const coreGeom = new THREE.SphereGeometry(49.0, 12, 12);
    const coreMat = new THREE.MeshBasicMaterial({
        color: 0x03030c,
        transparent: true,
        opacity: 0.85
    });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    globeScene.add(coreMesh);

    // Atmosphere Outer Glow mesh (Emerald green)
    const atmosGeom = new THREE.SphereGeometry(52.5, 12, 12);
    const atmosMat = new THREE.MeshBasicMaterial({
        color: 0x00f59b,
        wireframe: true,
        transparent: true,
        opacity: 0.05
    });
    const atmosMesh = new THREE.Mesh(atmosGeom, atmosMat);
    globeScene.add(atmosMesh);
    
    // Anomaly Markers on Globe
    const markers = [
        { lat: -23.472, lon: -68.349, color: 0x00f59b }, // Atacama
        { lat: -12.894, lon: -69.912, color: 0xef4444 }, // Madre de Dios
        { lat: 50.412, lon: 14.903, color: 0xf59e0b }   // Czechia
    ];
    
    markers.forEach(m => {
        const phi = (90 - m.lat) * (Math.PI / 180);
        const theta = (m.lon + 180) * (Math.PI / 180);
        
        const r = 50;
        const x = -(r * Math.sin(phi) * Math.sin(theta));
        const y = r * Math.cos(phi);
        const z = r * Math.sin(phi) * Math.cos(theta);
        
        const markerGeom = new THREE.SphereGeometry(1.8, 6, 6);
        const markerMat = new THREE.MeshBasicMaterial({ color: m.color, transparent: true, opacity: 0.95 });
        const markerMesh = new THREE.Mesh(markerGeom, markerMat);
        markerMesh.position.set(x, y, z);
        globeMesh.add(markerMesh);
    });
    
    // Orbit Rings
    orbitLinesGroup = new THREE.Group();
    globeScene.add(orbitLinesGroup);
    
    const orbitColors = [0xd4af37, 0x00f59b, 0x3b82f6];
    const laserBeams = [];

    for (let o = 0; o < 3; o++) {
        const orbitRadius = 65 + o * 6;
        const orbitGeom = new THREE.BufferGeometry();
        const points = [];
        const numPoints = 48;
        
        for (let i = 0; i <= numPoints; i++) {
            const angle = (i / numPoints) * Math.PI * 2;
            points.push(new THREE.Vector3(
                Math.cos(angle) * orbitRadius,
                0,
                Math.sin(angle) * orbitRadius
            ));
        }
        orbitGeom.setFromPoints(points);
        const orbitMat = new THREE.LineBasicMaterial({
            color: orbitColors[o],
            transparent: true,
            opacity: 0.22
        });
        const orbitLine = new THREE.Line(orbitGeom, orbitMat);
        
        if (o === 0) orbitLine.rotation.x = Math.PI / 4.2;
        if (o === 1) orbitLine.rotation.z = Math.PI / 3.1;
        if (o === 2) orbitLine.rotation.y = Math.PI / 5.5;
        
        orbitLinesGroup.add(orbitLine);
        
        const satGroup = new THREE.Group();
        const bodyGeom = new THREE.BoxGeometry(2.2, 1.2, 1.2);
        const bodyMat = new THREE.MeshBasicMaterial({ color: orbitColors[o] });
        const bodyMesh = new THREE.Mesh(bodyGeom, bodyMat);
        satGroup.add(bodyMesh);

        // Solar panels
        const panelGeom = new THREE.BoxGeometry(2.8, 0.6, 0.1);
        const panelMat = new THREE.MeshBasicMaterial({ color: 0x223344, transparent: true, opacity: 0.8 });
        const leftPanel = new THREE.Mesh(panelGeom, panelMat);
        leftPanel.position.x = -2.2;
        const rightPanel = leftPanel.clone();
        rightPanel.position.x = 2.2;
        satGroup.add(leftPanel);
        satGroup.add(rightPanel);
        
        orbitLine.add(satGroup);
        
        satGroup.userData = { 
            angle: Math.random() * Math.PI * 2, 
            radius: orbitRadius, 
            speed: 0.005 + Math.random() * 0.004 
        };

        // Scanning Laser
        const beamGeom = new THREE.BufferGeometry();
        const beamPoints = [new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,0)];
        beamGeom.setFromPoints(beamPoints);
        
        const beamMat = new THREE.LineBasicMaterial({
            color: orbitColors[o],
            transparent: true,
            opacity: 0.4
        });
        const beamLine = new THREE.Line(beamGeom, beamMat);
        globeScene.add(beamLine);
        
        laserBeams.push({
            line: beamLine,
            satGroup: satGroup,
            orbitLine: orbitLine
        });
    }
    
    function animateGlobe() {
        requestAnimationFrame(animateGlobe);
        globeMesh.rotation.y += 0.0012;
        globeMesh.rotation.x += 0.0002;
        atmosMesh.rotation.y -= 0.0004;
        
        laserBeams.forEach(beam => {
            const sat = beam.satGroup;
            if (sat.userData) {
                sat.userData.angle += sat.userData.speed;
                sat.position.set(
                    Math.cos(sat.userData.angle) * sat.userData.radius,
                    0,
                    Math.sin(sat.userData.angle) * sat.userData.radius
                );
                sat.rotation.y = -sat.userData.angle;

                const satWorldPos = new THREE.Vector3();
                sat.getWorldPosition(satWorldPos);
                const surfacePos = satWorldPos.clone().normalize().multiplyScalar(50);
                
                beam.line.geometry.setFromPoints([satWorldPos, surfacePos]);
                beam.line.material.opacity = 0.15 + Math.abs(Math.sin(Date.now() * 0.002)) * 0.45;
            }
        });
        
        globeRenderer.render(globeScene, globeCamera);
    }
    animateGlobe();
    
    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            const w = entry.contentRect.width || 320;
            const h = entry.contentRect.height || 320;
            if (globeRenderer && globeCamera) {
                globeRenderer.setSize(w, h);
                globeCamera.aspect = w / h;
                globeCamera.updateProjectionMatrix();
            }
        }
    });
    resizeObserver.observe(container);
}

// 3. PIPELINE INTERACTIVE SELECTOR
function initPipelineInteractivity() {
    const nodes = ["node-raw", "node-ingestion", "node-ai", "node-allocator"];
    
    nodes.forEach(nodeId => {
        const el = document.getElementById(nodeId);
        if (!el) return;
        
        el.addEventListener("click", () => {
            const specs = pipelineNodes[nodeId];
            if (!specs) return;
            
            // Highlight selected node with stroke adjustments
            nodes.forEach(id => {
                const subEl = document.getElementById(id);
                if (!subEl) return;
                const circle = subEl.querySelector("circle");
                const rect = subEl.querySelector("rect");
                const polygon = subEl.querySelector("polygon");
                if (circle) circle.setAttribute("stroke-width", "2");
                if (rect) rect.setAttribute("stroke-width", "1.5");
                if (polygon) polygon.setAttribute("stroke-width", "1.5");
            });

            const circle = el.querySelector("circle");
            const rect = el.querySelector("rect");
            const polygon = el.querySelector("polygon");
            if (circle) circle.setAttribute("stroke-width", "4");
            if (rect) rect.setAttribute("stroke-width", "3.5");
            if (polygon) polygon.setAttribute("stroke-width", "3.5");

            // Update details
            document.getElementById("pipeline-node-name").innerText = specs.name;
            document.getElementById("pipeline-node-desc").innerText = specs.desc;
            
            // Build parameters HTML
            const metaContainer = document.getElementById("pipeline-node-meta");
            metaContainer.innerHTML = "";
            specs.meta.forEach(m => {
                const p = document.createElement("p");
                p.innerText = m;
                metaContainer.appendChild(p);
            });

            const statusBadge = document.getElementById("pipeline-status-badge");
            statusBadge.innerText = specs.status;
        });
    });
    
    // Trigger initial node select
    const initialNode = document.getElementById("node-raw");
    if (initialNode) initialNode.click();
}

// 4. VANGUARD FUND SCREENER CONTROLLER
function initScreenerTable() {
    const tableBody = document.getElementById("vanguard-fund-table-body");
    if (!tableBody) return;
    
    tableBody.innerHTML = "";
    
    vanguardFunds.forEach(fund => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-900 hover:bg-spacemid/40 transition-colors cursor-pointer";
        tr.dataset.ticker = fund.ticker;
        
        // Highlight rows with warnings
        const expenseClass = fund.expense_ratio > 0.20 ? "text-critical font-bold" : "text-slate-350";
        const historyText = fund.history ? `${fund.history} Yrs` : "N/A";
        const historyClass = fund.history < 3 ? "text-critical font-bold" : "text-slate-350";
        
        const return3y = fund.r3y !== null ? `${fund.r3y}%` : "--";
        const return10y = fund.r10y !== null ? `${fund.r10y}%` : "--";
        
        let statusBadge = `<span class="bg-safe/10 border border-safe/30 text-safe text-[9px] px-1.5 py-0.5 rounded font-bold">APPROVED</span>`;
        if (fund.history < 3) {
            statusBadge = `<span class="bg-critical/10 border border-critical/30 text-critical text-[9px] px-1.5 py-0.5 rounded font-bold" title="Fail: Under 3Y track record">HIST FAIL</span>`;
        } else if (fund.expense_ratio > 0.20) {
            statusBadge = `<span class="bg-critical/10 border border-critical/30 text-critical text-[9px] px-1.5 py-0.5 rounded font-bold" title="Fail: Expense ratio above 0.20%">FEE FAIL</span>`;
        }

        const isChecked = fund.ticker === selectedFundTicker ? "checked" : "";

        tr.innerHTML = `
            <td class="py-3 px-3 font-bold text-white">${fund.ticker}</td>
            <td class="py-3 px-3 text-slate-300 max-w-[150px] truncate" title="${fund.name}">${fund.name}</td>
            <td class="py-3 px-3 text-center text-slate-450">${fund.vehicle}</td>
            <td class="py-3 px-3 text-right ${expenseClass}">${fund.expense_ratio.toFixed(2)}%</td>
            <td class="py-3 px-3 text-right">${return3y}</td>
            <td class="py-3 px-3 text-right">${return10y}</td>
            <td class="py-3 px-3 text-right text-slate-450">$${fund.aum.toFixed(1)}B</td>
            <td class="py-3 px-3 text-center">${statusBadge}</td>
            <td class="py-3 px-3 text-center">
                <input type="radio" name="selected-fund" value="${fund.ticker}" ${isChecked} class="accent-gold cursor-pointer" />
            </td>
        `;
        
        // Clicking row selects fund
        tr.addEventListener("click", (e) => {
            if (e.target.tagName !== "INPUT") {
                const radio = tr.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    selectFund(fund.ticker);
                }
            }
        });
        
        tableBody.appendChild(tr);
    });

    // Handle radio changes
    document.getElementsByName("selected-fund").forEach(radio => {
        radio.addEventListener("change", () => {
            if (radio.checked) {
                selectFund(radio.value);
            }
        });
    });

    // Run initial calculations
    calculateAttribution();
}

function selectFund(ticker) {
    selectedFundTicker = ticker;
    document.getElementById("fund-calc-ticker").innerText = ticker;
    calculateAttribution();
}

function calculateAttribution() {
    const capitalInput = document.getElementById("portfolio-capital");
    if (!capitalInput) return;
    
    let capital = parseFloat(capitalInput.value) || 250;
    
    const fund = vanguardFunds.find(f => f.ticker === selectedFundTicker);
    if (!fund) return;
    
    // Simulated Holding size in Millions
    const simHoldingSize = capital * fund.weight;
    
    // 1. Check Chief Risk Officer warning
    const croAlert = document.getElementById("cro-alert-banner");
    const valHoldingSizeEl = document.getElementById("val-holdingsize");
    
    valHoldingSizeEl.innerText = `$${simHoldingSize.toFixed(1)}M`;
    if (simHoldingSize > 50.0) {
        if (croAlert) croAlert.classList.remove("hidden");
        valHoldingSizeEl.className = "font-bold text-critical text-sm animate-pulse";
    } else {
        if (croAlert) croAlert.classList.add("hidden");
        valHoldingSizeEl.className = "font-bold text-white text-sm";
    }
    
    // 2. Load metrics
    document.getElementById("val-sharpe").innerText = fund.sharpe !== null ? fund.sharpe.toFixed(2) : "N/A";
    document.getElementById("val-beta").innerText = fund.beta.toFixed(2);
    
    let maxDrawdownText = "--";
    if (fund.ticker === "VOO") maxDrawdownText = "-24.4%";
    else if (fund.ticker === "VGT") maxDrawdownText = "-29.8%";
    else if (fund.ticker === "VTI") maxDrawdownText = "-25.1%";
    else if (fund.ticker === "BND") maxDrawdownText = "-13.2%";
    else if (fund.ticker === "VMFXX") maxDrawdownText = "0.0%";
    else if (fund.ticker === "VINF") maxDrawdownText = "-32.5%";
    document.getElementById("val-drawdown").innerText = maxDrawdownText;
    
    // 3. Investment Principles Checks
    // Goals Check (mandate: Long/Short Equity)
    const goalsCheck = document.getElementById("check-goals");
    if (fund.category === "Money Market" || fund.category === "Intermediate Core Bond") {
        goalsCheck.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> MISMATCH`;
        goalsCheck.className = "text-warning font-bold";
    } else {
        goalsCheck.innerHTML = `<i class="fa-solid fa-circle-check"></i> PASS`;
        goalsCheck.className = "text-safe font-bold";
    }

    // Balance Check
    const balanceCheck = document.getElementById("check-balance");
    if (fund.beta > 0.05 && fund.beta < 1.20) {
        balanceCheck.innerHTML = `<i class="fa-solid fa-circle-check"></i> PASS`;
        balanceCheck.className = "text-safe font-bold";
    } else {
        balanceCheck.innerHTML = `<i class="fa-solid fa-circle-check"></i> PASS (BALLAST)`;
        balanceCheck.className = "text-safe/80 font-bold";
    }

    // Costs Check (<= 0.20%)
    const costsCheck = document.getElementById("check-costs");
    if (fund.expense_ratio <= 0.20) {
        costsCheck.innerHTML = `<i class="fa-solid fa-circle-check"></i> PASS`;
        costsCheck.className = "text-safe font-bold";
    } else {
        costsCheck.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> FAIL`;
        costsCheck.className = "text-critical font-bold";
    }

    // Discipline Check (>= 3 Yrs)
    const disciplineCheck = document.getElementById("check-discipline");
    if (fund.history >= 3) {
        disciplineCheck.innerHTML = `<i class="fa-solid fa-circle-check"></i> PASS`;
        disciplineCheck.className = "text-safe font-bold";
    } else {
        disciplineCheck.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> FAIL`;
        disciplineCheck.className = "text-critical font-bold";
    }

    // 4. Update Recommendation card
    document.getElementById("calc-recommendation").innerText = fund.recommendation;
    if (fund.recommendation === "OVERWEIGHT") {
        document.getElementById("calc-recommendation").className = "text-safe font-bold px-2 py-0.5 bg-safe/10 border border-safe/30 rounded text-[9px]";
    } else if (fund.recommendation === "NEUTRAL") {
        document.getElementById("calc-recommendation").className = "text-gold font-bold px-2 py-0.5 bg-gold/10 border border-gold/30 rounded text-[9px]";
    } else if (fund.recommendation === "UNDERWEIGHT") {
        document.getElementById("calc-recommendation").className = "text-warning font-bold px-2 py-0.5 bg-warning/10 border border-warning/30 rounded text-[9px]";
    } else {
        document.getElementById("calc-recommendation").className = "text-critical font-bold px-2 py-0.5 bg-critical/10 border border-critical/30 rounded text-[9px]";
    }
    document.getElementById("calc-rationale").innerText = fund.rationale;
    
    // Auto-update JSON Output in background
    compileJSONOutput();
}

function compileJSONOutput() {
    const fund = vanguardFunds.find(f => f.ticker === selectedFundTicker);
    if (!fund) return;
    
    const capitalInput = document.getElementById("portfolio-capital");
    let capital = parseFloat(capitalInput.value) || 250;
    const simHoldingSize = capital * fund.weight;
    
    let riskFlags = [];
    if (simHoldingSize > 50.0) riskFlags.push("OVER_LIMIT_50M");
    if (fund.history < 3) riskFlags.push("INSUFFICIENT_HISTORY");
    if (fund.expense_ratio > 0.20) riskFlags.push("HIGH_EXPENSE_RATIO");
    if (fund.category === "Money Market" || fund.category === "Intermediate Core Bond") riskFlags.push("MANDATE_STRATEGY_MISMATCH");

    // Formulate JSON string
    const jsonOutput = {
        ticker: fund.ticker,
        fund_name: fund.name,
        vehicle: fund.vehicle,
        category: fund.category,
        expense_ratio_pct: fund.expense_ratio,
        performance: {
            "1y": fund.r1y,
            "3y": fund.r3y,
            "5y": fund.r5y,
            "10y": fund.r10y
        },
        risk_metrics: {
            sharpe_3y: fund.sharpe,
            std_dev_3y: fund.ticker === "VOO" ? 17.50 : (fund.ticker === "VGT" ? 22.40 : (fund.ticker === "VTI" ? 18.10 : 8.40)),
            max_drawdown: fund.ticker === "VOO" ? -24.40 : (fund.ticker === "VGT" ? -29.80 : (fund.ticker === "VTI" ? -25.10 : -13.20)),
            beta_vs_benchmark: fund.beta
        },
        aum_bn: fund.aum,
        track_record_yrs: Math.floor(fund.history),
        lipper_percentile_10y: fund.lipper || 0,
        recommendation: fund.recommendation,
        rationale: fund.rationale,
        risk_flags: riskFlags,
        data_as_of: new Date().toISOString()
    };

    const container = document.getElementById("json-compliance-output");
    if (container) {
        container.innerText = `<fund_analysis>\n${JSON.stringify(jsonOutput, null, 2)}\n</fund_analysis>`;
    }
}

// 5. MAP AND GEOSPATIAL ANOMALIES INTERCONNECTIVITY
function initMap() {
    const mapContainer = document.getElementById("map");
    if (!mapContainer) return;
    
    // Set up Leaflet map center
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([15, 0], 2);
    
    darkBasemapLayer = L.tileLayer(darkMatterTilesUrl, {
        maxZoom: 18
    }).addTo(map);
    
    satelliteBasemapLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18
    });
}

function initMinimap() {
    const minimapContainer = document.getElementById("minimap");
    if (!minimapContainer) return;
    
    const mini = L.map('minimap', {
        zoomControl: false,
        attributionControl: false,
        dragging: false,
        touchZoom: false,
        scrollWheelZoom: false
    }).setView([15, 0], 0);
    
    L.tileLayer(darkMatterTilesUrl, {
        maxZoom: 18
    }).addTo(mini);

    // Sync views
    map.on('move', () => {
        mini.setView(map.getCenter(), Math.max(0, map.getZoom() - 3));
    });
}

async function loadDashboardData() {
    try {
        const res = await fetch("data/anomalies.json");
        anomaliesData = await res.json();
        console.log("Anomalies loaded:", anomaliesData.length);
        renderAnomalyMarkers();
        selectAnomaly(anomaliesData[0].id);
    } catch (e) {
        console.error("Failed to load anomalies.json:", e);
    }
}

function renderAnomalyMarkers() {
    mapMarkers.forEach(m => map.removeLayer(m.markerObj));
    mapMarkers = [];

    anomaliesData.forEach(anomaly => {
        // Different classes based on types
        let pulseClass = "pulse-marker-icon";
        if (anomaly.id.includes("lithium")) pulseClass = "pulse-marker-icon pulse-marker-lithium";
        else if (anomaly.id.includes("night")) pulseClass = "pulse-marker-icon pulse-marker-ntl";

        const icon = L.divIcon({
            className: pulseClass,
            iconSize: [12, 12]
        });

        const marker = L.marker(anomaly.coordinates, { icon: icon }).addTo(map);
        
        marker.on("click", () => {
            selectAnomaly(anomaly.id);
        });

        mapMarkers.push({
            id: anomaly.id,
            markerObj: marker,
            data: anomaly
        });
    });
}

function selectAnomaly(id) {
    const match = mapMarkers.find(m => m.id === id);
    if (!match) return;
    
    currentSelectedAnomaly = match.data;
    
    // Zoom map slightly
    map.setView(currentSelectedAnomaly.coordinates, 5);
    
    // Update coordinates display
    document.getElementById("hud-coordinates").innerText = `${currentSelectedAnomaly.coordinates[0].toFixed(5)}, ${currentSelectedAnomaly.coordinates[1].toFixed(5)}`;
    
    // Update Side drawer
    document.getElementById("anomaly-title").innerText = currentSelectedAnomaly.region;
    document.getElementById("anomaly-region").innerHTML = `<i class="fa-solid fa-location-dot text-gold mr-1"></i> GPS: ${currentSelectedAnomaly.coordinates[0]}, ${currentSelectedAnomaly.coordinates[1]}`;
    
    // Confidence Percentage
    const confVal = Math.round(currentSelectedAnomaly.confidence * 100);
    document.getElementById("confidence-percentage").innerText = `${confVal}%`;
    document.getElementById("confidence-bar").style.width = `${confVal}%`;
    
    // Badge
    const badge = document.getElementById("anomaly-badge");
    badge.innerText = currentSelectedAnomaly.verification.status;
    if (currentSelectedAnomaly.verification.status === "Verified") {
        badge.className = "bg-safe/10 border border-safe/30 text-safe text-[9px] font-code px-2 py-0.5 rounded uppercase";
    } else {
        badge.className = "bg-warning/10 border border-warning/30 text-warning text-[9px] font-code px-2 py-0.5 rounded uppercase";
    }

    // Stats
    document.getElementById("metric-zscore").innerText = currentSelectedAnomaly.z_score.toFixed(2);
    document.getElementById("metric-uncertainty").innerText = `${(currentSelectedAnomaly.uncertainty * 100).toFixed(1)}%`;

    // Map matching corporate equity symbol to show investor integration
    let holdingsMatchText = "No direct holding matches strategy overlay.";
    if (currentSelectedAnomaly.id.includes("lithium")) {
        holdingsMatchText = "<strong>Apex Holding Match: SQM / Albemarle (NYSE: ALB)</strong>.<br>Lithium pond expansion correlates directly with increased capacity contracts. Positive return attribution mapped to VGT/VOO weights.";
    } else if (currentSelectedAnomaly.id.includes("mining")) {
        holdingsMatchText = "<strong>Apex Holding Match: Freeport-McMoRan (NYSE: FCX)</strong>.<br>Sensing clearings flag copper mining output increase. Downstream logistics verify strong sector tailwinds.";
    } else if (currentSelectedAnomaly.id.includes("night")) {
        holdingsMatchText = "<strong>Apex Holding Match: European Automotive Index (Porsche/Škoda)</strong>.<br>Industrial night illuminations reveal production spikes correlating to automotive output rebounds in Q2 2025.";
    }

    document.getElementById("anomaly-description").innerHTML = `
        <p class="text-slate-350 leading-relaxed">${currentSelectedAnomaly.details}</p>
        <div class="mt-3 p-2 bg-void/50 rounded border border-gold/15 text-[10.5px]">
            ${holdingsMatchText}
        </div>
    `;

    // Update Radar Chart signatures
    updateRadarChart(currentSelectedAnomaly.spectral_profile);
}

// 6. RADAR CHART SIGNATURE (Chart.js)
function initRadarChart() {
    const ctx = document.getElementById("radarChart");
    if (!ctx) return;
    
    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['NDVI (Veg)', 'NDWI (Water)', 'BSI (Exposed Soil)'],
            datasets: [{
                label: 'Spectral Index Signature',
                data: [0, 0, 0],
                backgroundColor: 'rgba(0, 245, 155, 0.15)',
                borderColor: '#00f59b',
                borderWidth: 1.5,
                pointBackgroundColor: '#d4af37',
                pointBorderColor: '#ffffff'
            }]
        },
        options: {
            plugins: {
                legend: { display: false }
            },
            scales: {
                r: {
                    angleLines: { color: 'rgba(212, 175, 55, 0.1)' },
                    grid: { color: 'rgba(212, 175, 55, 0.1)' },
                    pointLabels: {
                        color: '#8899bb',
                        font: { size: 9, family: 'JetBrains Mono' }
                    },
                    ticks: { display: false }
                }
            }
        }
    });
}

function updateRadarChart(profile) {
    if (!radarChartInstance || !profile) return;
    
    radarChartInstance.data.datasets[0].data = [
        profile.ndvi || 0,
        profile.ndwi || 0,
        profile.bsi || 0
    ];
    radarChartInstance.update();
}

// 7. THESIS ACADEMIC CHAPTERS LOADER
function initChapters() {
    const select = document.getElementById("chapter-select");
    if (!select) return;
    
    select.addEventListener("change", (e) => {
        loadChapterContent(e.target.value);
    });

    // Load initial Chapter
    loadChapterContent("1");
}

function loadChapterContent(chapterId) {
    const titleEl = document.getElementById("chapter-title");
    const contentEl = document.getElementById("chapter-content");
    const badgeEl = document.getElementById("chapter-node-badge");
    
    const db = currentLang === 'CS' ? academicChaptersCS : (currentLang === 'ES' ? academicChaptersES : academicChapters);
    const data = db[chapterId];
    if (!data) return;
    
    titleEl.innerText = data.title;
    badgeEl.innerText = `§${chapterId}.0 ACTIVE`;
    
    contentEl.innerHTML = "";
    data.sections.forEach(sec => {
        const div = document.createElement("div");
        div.className = "space-y-1.5";
        div.innerHTML = `
            <h4 class="font-display font-semibold text-white text-[12px] flex items-center">
                <i class="fa-solid fa-angle-right text-gold mr-1.5 text-[10px]"></i>
                ${sec.name}
            </h4>
            <p class="text-slate-400 pl-4">${sec.text}</p>
        `;
        contentEl.appendChild(div);
    });
}

// 8. EVENT LISTENERS SETUP
function setupEventListeners() {
    // Portfolio Capital Slider/Input
    const capitalInput = document.getElementById("portfolio-capital");
    if (capitalInput) {
        capitalInput.addEventListener("input", calculateAttribution);
    }
    
    // Map Basemaps Layer toggles
    const btnDark = document.getElementById("btn-basemap-dark");
    const btnSat = document.getElementById("btn-basemap-sat");
    
    if (btnDark && btnSat) {
        btnDark.addEventListener("click", () => {
            btnDark.className = "px-2 py-0.5 rounded bg-gold text-void font-bold shadow-[0_0_8px_rgba(212,175,55,0.4)]";
            btnSat.className = "px-2 py-0.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-all";
            map.removeLayer(satelliteBasemapLayer);
            darkBasemapLayer.addTo(map);
        });

        btnSat.addEventListener("click", () => {
            btnSat.className = "px-2 py-0.5 rounded bg-gold text-void font-bold shadow-[0_0_8px_rgba(212,175,55,0.4)]";
            btnDark.className = "px-2 py-0.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-all";
            map.removeLayer(darkBasemapLayer);
            satelliteBasemapLayer.addTo(map);
        });
    }

    // Heatmap Toggle
    const btnHeatmap = document.getElementById("btn-toggle-heatmap");
    if (btnHeatmap) {
        btnHeatmap.addEventListener("click", () => {
            heatmapActive = !heatmapActive;
            if (heatmapActive) {
                btnHeatmap.innerText = "ON";
                btnHeatmap.className = "ml-2 px-2 py-0.5 rounded bg-gold text-void font-bold shadow-[0_0_8px_rgba(212,175,55,0.4)]";
                
                // Construct points
                const pts = anomaliesData.map(a => [a.coordinates[0], a.coordinates[1], a.confidence * 2]);
                heatmapLayer = L.heatLayer(pts, { radius: 35, blur: 20 }).addTo(map);
            } else {
                btnHeatmap.innerText = "OFF";
                btnHeatmap.className = "ml-2 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 hover:border-gold transition-all text-white";
                if (heatmapLayer) {
                    map.removeLayer(heatmapLayer);
                    heatmapLayer = null;
                }
            }
        });
    }

    // Copy to clipboard utility
    const btnCopy = document.getElementById("btn-copy-json");
    if (btnCopy) {
        btnCopy.addEventListener("click", () => {
            const pre = document.getElementById("json-compliance-output");
            if (!pre) return;
            
            navigator.clipboard.writeText(pre.innerText)
                .then(() => {
                    const label = document.getElementById("copy-btn-text");
                    label.innerText = "Copied!";
                    btnCopy.className = "px-3 py-1 rounded bg-safe text-void font-bold transition-all flex items-center space-x-1 shadow-md";
                    
                    setTimeout(() => {
                        label.innerText = "Copy JSON";
                        btnCopy.className = "px-3 py-1 rounded bg-slate-800 text-gold border border-slate-700 hover:border-gold hover:bg-spacemid transition-all flex items-center space-x-1 shadow-md";
                    }, 2000);
                })
                .catch(err => console.error("Clipboard copy failed:", err));
        });
    }

    // Map Layers buttons
    const btnAll = document.getElementById("btn-layer-all");
    const btnChile = document.getElementById("btn-layer-all-chile");
    const btnPeru = document.getElementById("btn-layer-all-peru");
    const btnCzechia = document.getElementById("btn-layer-all-czech");

    const clearActiveGridFilters = () => {
        [btnAll, btnChile, btnPeru, btnCzechia].forEach(btn => {
            if (btn) btn.className = "px-3 py-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-all";
        });
    };

    if (btnAll) {
        btnAll.addEventListener("click", () => {
            clearActiveGridFilters();
            btnAll.className = "px-3 py-1 rounded bg-gold text-void font-bold transition-all shadow-[0_0_10px_rgba(212,175,55,0.2)]";
            map.setView([15, 0], 2);
        });
    }
    if (btnChile) {
        btnChile.addEventListener("click", () => {
            clearActiveGridFilters();
            btnChile.className = "px-3 py-1 rounded bg-gold text-void font-bold transition-all shadow-[0_0_10px_rgba(212,175,55,0.2)]";
            const anomaly = anomaliesData.find(a => a.id.includes("lithium"));
            if (anomaly) selectAnomaly(anomaly.id);
        });
    }
    if (btnPeru) {
        btnPeru.addEventListener("click", () => {
            clearActiveGridFilters();
            btnPeru.className = "px-3 py-1 rounded bg-gold text-void font-bold transition-all shadow-[0_0_10px_rgba(212,175,55,0.2)]";
            const anomaly = anomaliesData.find(a => a.id.includes("mining"));
            if (anomaly) selectAnomaly(anomaly.id);
        });
    }
    if (btnCzechia) {
        btnCzechia.addEventListener("click", () => {
            clearActiveGridFilters();
            btnCzechia.className = "px-3 py-1 rounded bg-gold text-void font-bold transition-all shadow-[0_0_10px_rgba(212,175,55,0.2)]";
            const anomaly = anomaliesData.find(a => a.id.includes("night"));
            if (anomaly) selectAnomaly(anomaly.id);
        });
    }

    // Language Toggle
    const btnLang = document.getElementById("lang-toggle");
    if (btnLang) {
        btnLang.addEventListener("click", () => {
            if (currentLang === 'EN') {
                currentLang = 'CS';
            } else if (currentLang === 'CS') {
                currentLang = 'ES';
            } else {
                currentLang = 'EN';
            }
            localStorage.setItem("orbital_lang", currentLang);
            document.getElementById("lang-label").innerText = currentLang;
            updateUILanguage();
            loadChapterContent(document.getElementById("chapter-select").value);
        });
    }

    // Init Chapters select
    initChapters();
}

function updateUILanguage() {
    const isEn = currentLang === 'EN';
    const isCs = currentLang === 'CS';
    
    document.getElementById("hero-badge-label").innerText = isEn ? "Y Combinator Investor Preview" : (isCs ? "Y Combinator Náhled pro investory" : "Vista previa de inversores de Y Combinator");
    document.getElementById("hero-title-prefix").innerText = isEn ? "Institutional" : (isCs ? "Institucionální" : "Telemetría");
    document.getElementById("typewriter-headline").innerText = isEn ? "Venture Telemetry" : (isCs ? "Investiční Telemetrie" : "de Inversión Institucional");
    
    document.getElementById("hero-subtitle").innerText = isEn ? 
        "Apex Capital Partners' proprietary pipeline translating Earth Observation (EO) satellite reflectance bands and night-lights datasets into institutional alpha. Directly evaluate Vanguard fund efficiencies, perform compliance checks, and trace asset correlations." :
        (isCs ? 
            "Vlastní datová pipeline společnosti Apex Capital Partners pro převod spektrálních pásem satelitů dálkového průzkumu Země (EO) a nočního osvětlení na investiční alfu. Přímé hodnocení efektivnosti fondů Vanguard, provádění kontrol shody a analýza korelací aktiv." :
            "La pipeline patentada de Apex Capital Partners que traduce las bandas de reflectancia de satélites de observación de la Tierra (EO) y conjuntos de datos de luces nocturnas en alfa institucional. Evalúe directamente las eficiencias de los fondos Vanguard, realice comprobaciones de cumplimiento y analice las correlaciones de activos.");

    document.getElementById("lang-label").innerText = currentLang;
}

function checkLiveAPIHealth() {
    const apis = {
        "gee": "https://earthengine.googleapis.com/",
        "cdse": "https://catalogue.dataspace.copernicus.eu/odata/v1/",
        "nasa": "https://cmr.earthdata.nasa.gov/search/",
        "wb": "https://api.worldbank.org/v2/country/CZE?format=json",
        "com": "https://comtradeapi.un.org/data/v1/get/C/A/282520?period=2024"
    };

    Object.entries(apis).forEach(([name, url]) => {
        const dot = document.getElementById(`api-status-${name}`);
        if (!dot) return;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);

        fetch(url, { method: "GET", mode: "no-cors", signal: controller.signal })
            .then(() => {
                clearTimeout(timeoutId);
                dot.className = "w-2 h-2 rounded-full bg-safe status-dot-pulse"; // green (success/active)
            })
            .catch((err) => {
                clearTimeout(timeoutId);
                console.warn(`API live status check failed for ${name}:`, err);
                dot.className = "w-2 h-2 rounded-full bg-critical status-dot-pulse"; // red (offline/timeout)
            });
    });
}
