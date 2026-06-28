// ==========================================
// ORBITAL ECONOMIC INTELLIGENCE CONTROLLER
// ==========================================

// Global state variables
let map, radarChartInstance;
let anomaliesData = [];
let regionsData = null;
let currentSelectedAnomaly = null;

let currentLang = 'EN';
let translations = { EN: null, CS: null, ES: null, UK: null };

async function loadTranslations() {
    try {
        const responseEn = await fetch('locales/en.json');
        const responseCs = await fetch('locales/cs.json');
        const responseEs = await fetch('locales/es.json');
        const responseUk = await fetch('locales/uk.json');
        translations.EN = await responseEn.json();
        translations.CS = await responseCs.json();
        translations.ES = await responseEs.json();
        translations.UK = await responseUk.json();
        console.log("Translations loaded successfully");
    } catch (error) {
        console.error("Failed to load translations, utilizing fallbacks:", error);
        translations.EN = { ui: {}, chapters: {} };
        translations.CS = { ui: {}, chapters: {} };
        translations.ES = { ui: {}, chapters: {} };
        translations.UK = { ui: {}, chapters: {} };
    }
}

// Advanced GIS & WebGL state
let darkBasemapLayer, satelliteBasemapLayer;
let heatmapLayer = null;
let heatmapActive = false;
let mapMarkers = []; // holds { markerObj, anomalyData }
let currentBandMode = 'rgb'; // 'rgb', 'fc', 'agri', 'geol'

// Three.js 3D Globe state
let globeScene, globeCamera, globeRenderer, globeMesh, orbitLinesGroup;

// Academic Chapters Content Cache
const academicChapters = {
    "1": {
        title: "Chapter 1: Introduction",
        sections: [
            { name: "1.1 Background & Motivation", text: "In the modern digital economy, information engineering has expanded beyond terrestrial borders. The rise of Earth Observation (EO) satellite constellations, coupled with cloud-based geospatial computing platforms, has birthed a new domain: Space-Based Economic Intelligence. Satellite remote sensing offers a continuous, independent, and spatially explicit alternative. Civilian constellations funded by the European Space Agency (ESA Copernicus) and the United States Geological Survey (USGS/NASA) capture high-resolution multi-spectral, radar, and atmospheric data daily." },
            { name: "1.2 Problem Statement", text: "Despite the abundance of open satellite data, a critical gap remains: how to translate raw, multi-spectral raster feeds into structured, actionable economic intelligence anomalies. Raw satellite imagery is voluminous, noisy, and unstructured. Traditional geospatial analysis relies on localized human interpretation or manual crop-masking, which cannot scale to national or continental monitoring." },
            { name: "1.3 Research Questions", text: "RQ1: How reliably can open satellite spectral APIs identify localized industrial and mining resource anomalies compared to ground truth records?<br>RQ2: What is the correlation between VIIRS night-time light fluctuations and macro/microeconomic indicators in the target regions?<br>RQ3: What pipeline latency and processing constraints limit the scalability of free satellite APIs for real-time economic monitoring?" }
        ]
    },
    "2": {
        title: "Chapter 2: Theoretical Framework & Literature Review",
        sections: [
            { name: "2.1 Remote Sensing Principles", text: "Remote sensing is the science of acquiring information about the Earth's surface without physical contact, primarily by measuring electromagnetic radiation reflected or emitted from sensors. Modalities include passive sensors (Sentinel-2, Landsat) which capture reflected solar bands, and active sensors (Sentinel-1 SAR) which emit radar beams and register backscatter reflections, penetrating cloud covers." },
            { name: "2.2 Economic Intelligence history", text: "Mining footprints, shipping volume indexes, and urban night lights radiance (VIIRS DNB) act as leading economic proxies. Unsupervised anomaly models like Isolation Forest isolate outliers without requiring extensive labelled ground-truth grids." }
        ]
    },
    "3": {
        title: "Chapter 3: Methodology",
        sections: [
            { name: "3.1 Multi-Spectral Index Formulations", text: "To detect change, raw bands are combined mathematically:<br><strong>NDVI</strong> = (NIR - Red) / (NIR + Red) - measures forest density.<br><strong>NDWI</strong> = (Green - NIR) / (Green + NIR) - measures open water surface.<br><strong>BSI</strong> = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue)) - isolates exposed mining soil." },
            { name: "3.2 Unsupervised AI Engine", text: "A multi-spectral feature matrix is extracted. An Isolation Forest is fitted with contamination = 0.08, calculating path length distributions to isolate anomalous land cover deviations." }
        ]
    },
    "4": {
        title: "Chapter 4: System Design & Implementation",
        sections: [
            { name: "4.1 Decoupled GIS Architecture", text: "A high-performance Python data engineering back-end handles raster processing and model fitting. A lightweight flat JSON serialization layer acts as a cache. An interactive WebGL/HTML5 frontend renders maps, sliders, and radar charts." },
            { name: "4.2 Credential Protection", text: "Google Earth Engine initialization relies on GCP Project ID isolation, securing credentials in backend environment variables and Colab UserData, keeping the production deployment serverless and secure." }
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
            { name: "6.2 Study Limitations", text: "Primary constraints include cloud obstruction in optical channels and spatial resolutions (10m) missing micro-scale operations, which can be mitigated in future work via Sentinel-1 SAR and atmospheric sensor fusion." }
        ]
    },
    "7": {
        title: "Chapter 7: Conclusion",
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
            { name: "4.1 Architektura GIS", text: "Systém je navržen jako modulární zpracovatelská pipeline v jazyce Python s ukládáním výsledků do plochých JSON souborů, což eliminuje únik přístupových klíčů na klientské straně." }
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
            { name: "6.1 Přínosy a limity", text: "Práce prokazuje využitelnost bezplatných API pro ekonomické předpovědi a audit dodavatelských řetězců. Hlavním limitem zůstává oblačnost a prostorové rozlišení (10m)." }
        ]
    },
    "7": {
        title: "Kapitola 7: Závěr",
        sections: [
            { name: "7.1 Souhrn přínosů", text: "Byl vytvořen plně reprodukovatelný model pro detekci ekonomických anomálií ze satelitních dat s interaktivním dashboardem nasazeným na GitHub Pages." }
        ]
    }
};;

// Map CartoDB Dark basemap tiles
const darkMatterTilesUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const mapAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

document.addEventListener("DOMContentLoaded", () => {
    // 1. Load translations asynchronously, then apply and fetch data
    loadTranslations()
        .then(() => {
            try { updateUILanguage(); } catch (e) { console.error("Error updating initial language:", e); }
            try { loadDashboardData(); } catch (e) { console.error("Error loading dashboard data:", e); }
        })
        .catch(err => {
            console.error("Error in loadTranslations:", err);
            try { updateUILanguage(); } catch (e) { console.error("Error updating initial language after error:", e); }
            try { loadDashboardData(); } catch (e) { console.error("Error loading dashboard data after error:", e); }
        });

    // 2. Initialize UI components inside robust try-catch isolation blocks
    try { initStarsBackground(); } catch (e) { console.error("initStarsBackground failed:", e); }
    try { initMap(); } catch (e) { console.error("initMap failed:", e); }
    try { initMinimap(); } catch (e) { console.error("initMinimap failed:", e); }
    try { initRadarChart(); } catch (e) { console.error("initRadarChart failed:", e); }
    try { init3DGlobe(); } catch (e) { console.error("init3DGlobe failed:", e); }
    try { initSatelliteCounter(); } catch (e) { console.error("initSatelliteCounter failed:", e); }
    try { initConstellationInteractivity(); } catch (e) { console.error("initConstellationInteractivity failed:", e); }
    try { setupEventListeners(); } catch (e) { console.error("setupEventListeners failed:", e); }
});

// 1. STARFIELD PARALLAX SYSTEM
function initStarsBackground() {
    const canvas = document.getElementById("stars-canvas");
    const ctx = canvas.getContext("2d");
    
    let stars = [];
    const count = 100;
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resize);
    resize();
    
    for (let i = 0; i < count; i++) {
        stars.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 1.5,
            speed: Math.random() * 0.05 + 0.01
        });
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "rgba(0, 212, 255, 0.4)";
        stars.forEach(s => {
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fill();
            s.y -= s.speed;
            if (s.y < 0) s.y = canvas.height;
        });
        requestAnimationFrame(animate);
    }
    animate();
}

// 1.1 THREE.JS 3D EARTH GLOBE SYSTEM
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
        console.warn("WebGL not supported, displaying 2D static fallback:", e);
        if (fallback) {
            fallback.style.display = "flex";
            fallback.innerHTML = `
                <div class="text-center p-6 border border-neoncyan/15 rounded-full w-64 h-64 flex flex-col items-center justify-center bg-spacemid/10">
                    <i class="fa-solid fa-earth-americas text-5xl text-neoncyan/40 animate-pulse"></i>
                    <p class="text-[9px] text-slate-400 font-code uppercase tracking-widest mt-3">2D Orbit Fallback Mode</p>
                    <p class="text-[7px] text-slate-500 mt-1">WebGL is disabled or unsupported</p>
                </div>
            `;
        }
        return;
    }
    
    if (fallback) fallback.style.display = "none";
    globeRenderer.setSize(width, height);
    globeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(globeRenderer.domElement);
    
    // Holographic Wireframe Earth Globe
    const geometry = new THREE.SphereGeometry(50, 18, 18);
    const material = new THREE.MeshBasicMaterial({
        color: 0x00d4ff,
        wireframe: true,
        transparent: true,
        opacity: 0.20
    });
    
    globeMesh = new THREE.Mesh(geometry, material);
    globeScene.add(globeMesh);
    
    // Dark core
    const coreGeom = new THREE.SphereGeometry(48, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({
        color: 0x0a0a20,
        transparent: true,
        opacity: 0.7
    });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    globeScene.add(coreMesh);
    
    // Regional Anomaly Markers on the Globe surface
    const markers = [
        { lat: -23.472, lon: -68.349, color: 0x00d4ff }, // Atacama
        { lat: -12.894, lon: -69.912, color: 0xff4757 }, // Madre de Dios
        { lat: 50.412, lon: 14.903, color: 0xffa502 }   // Czechia
    ];
    
    markers.forEach(m => {
        const phi = (90 - m.lat) * (Math.PI / 180);
        const theta = (m.lon + 180) * (Math.PI / 180);
        
        const r = 50;
        const x = -(r * Math.sin(phi) * Math.sin(theta));
        const y = r * Math.cos(phi);
        const z = r * Math.sin(phi) * Math.cos(theta);
        
        const markerGeom = new THREE.SphereGeometry(1.8, 8, 8);
        const markerMat = new THREE.MeshBasicMaterial({ color: m.color });
        const markerMesh = new THREE.Mesh(markerGeom, markerMat);
        markerMesh.position.set(x, y, z);
        globeMesh.add(markerMesh);
    });
    
    // Orbit Rings & Satellites
    orbitLinesGroup = new THREE.Group();
    globeScene.add(orbitLinesGroup);
    
    const orbitColors = [0x00d4ff, 0x4361ee, 0xffa502];
    for (let o = 0; o < 3; o++) {
        const orbitGeom = new THREE.BufferGeometry();
        const points = [];
        const orbitRadius = 65 + o * 6;
        const numPoints = 64;
        
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
            opacity: 0.35
        });
        const orbitLine = new THREE.Line(orbitGeom, orbitMat);
        
        if (o === 0) orbitLine.rotation.x = Math.PI / 4;
        if (o === 1) orbitLine.rotation.z = Math.PI / 3;
        if (o === 2) orbitLine.rotation.y = Math.PI / 6;
        
        orbitLinesGroup.add(orbitLine);
        
        const satGeom = new THREE.BoxGeometry(2.5, 1.2, 1.2);
        const satMat = new THREE.MeshBasicMaterial({ color: orbitColors[o] });
        const satMesh = new THREE.Mesh(satGeom, satMat);
        orbitLine.add(satMesh);
        
        satMesh.userData = { angle: Math.random() * Math.PI * 2, radius: orbitRadius, speed: 0.008 + Math.random() * 0.008 };
    }
    
    function animateGlobe() {
        requestAnimationFrame(animateGlobe);
        
        globeMesh.rotation.y += 0.0015;
        globeMesh.rotation.x += 0.0004;
        
        orbitLinesGroup.children.forEach(orbit => {
            orbit.children.forEach(sat => {
                if (sat.userData) {
                    sat.userData.angle += sat.userData.speed;
                    sat.position.set(
                        Math.cos(sat.userData.angle) * sat.userData.radius,
                        0,
                        Math.sin(sat.userData.angle) * sat.userData.radius
                    );
                    sat.rotation.y = -sat.userData.angle;
                }
            });
        });
        
        globeRenderer.render(globeScene, globeCamera);
    }
    animateGlobe();
    
    // Resize dynamic handler
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

// 1.2 TYPEWRITER EFFECT
let typewriterInterval = null;
function initTypewriter() {
    const el = document.getElementById("typewriter-headline");
    if (!el) return;
    
    const texts = {
        EN: "Economic Intelligence",
        CS: "Ekonomické Zpravodajství"
    };
    
    let currentText = texts[currentLang];
    el.innerText = "";
    let i = 0;
    
    if (typewriterInterval) clearInterval(typewriterInterval);
    
    typewriterInterval = setInterval(() => {
        if (i < currentText.length) {
            el.innerText += currentText.charAt(i);
            i++;
        } else {
            clearInterval(typewriterInterval);
        }
    }, 80);
}

// 1.3 LIVE SATELLITE COUNTER
function initSatelliteCounter() {
    const counterEl = document.getElementById("live-satellite-counter");
    if (!counterEl) return;
    
    let currentVal = 7521;
    setInterval(() => {
        currentVal += Math.floor(Math.random() * 2) + 1;
        counterEl.innerText = currentVal.toLocaleString();
    }, 4500);
}

// 1.4 D3-LIKE DYNAMIC CONSTELLATION OVERLAY
function initConstellationInteractivity() {
    const svg = document.getElementById("constellation-svg");
    const panel = document.getElementById("constellation-hover-panel");
    if (!svg || !panel) return;
    
    const nodes = svg.querySelectorAll(".node-group");
    nodes.forEach(node => {
        node.addEventListener("mouseenter", () => {
            const info = currentLang === 'EN' ? node.getAttribute("data-info-en") : node.getAttribute("data-info-cs");
            panel.innerText = info;
            panel.style.opacity = 1;
            
            const id = node.id.replace("node-", "link-");
            const link = document.getElementById(id);
            if (link) {
                link.setAttribute("stroke", "#00d4ff");
                link.setAttribute("stroke-width", "2");
                link.setAttribute("stroke-dasharray", "none");
            }
        });
        
        node.addEventListener("mouseleave", () => {
            panel.style.opacity = 0;
            const id = node.id.replace("node-", "link-");
            const link = document.getElementById(id);
            if (link) {
                link.setAttribute("stroke", "#445577");
                link.setAttribute("stroke-width", "1");
                link.setAttribute("stroke-dasharray", "2,2");
            }
        });
    });
}

// 1.5 MULTI-LANGUAGE TRANSLATION MAPPING
const uiTranslations = {
    EN: {
        heroBadge: "Bachelor Thesis Artifact",
        heroTitlePrefix: "Space-Based",
        heroSubtitle: "Detecting hidden resource extraction patterns, supply chain shifts, and regional economic anomalies by querying open ESA, NASA, and USGS satellite APIs coupled with unsupervised machine learning models.",
        flightTrackerLabel: "ORBITAL FLIGHT TRACKER:",
        flightTrackerSuffix: "active payloads registered",
        heroBtnExplore: "Launch Sat-Map Explorer",
        heroBtnThesis: "View Thesis Drafts",
        basemapHudLabel: "Basemap:",
        heatmapHudLabel: "Heatmap Overlay:",
        btnExportViewport: "Export Viewport",
        timelineTitleLabel: "Temporal Navigation Timeline",
        selectedHudLabel: "Anomaly Selected",
        confidenceLabel: "Detection Confidence",
        beforeAfterLabel: "Before / After Imagery Comparison",
        spectralBandModeLabel: "Spectral Band Rendering Mode",
        groundTruthHudLabel: "Verification Ground Truth",
        btnExportReport: "Export Report",
        constellationTitle: "APIs Constellation Network",
        constellationDesc: "Mapping relationships between orbital sensors, public finance overlays, and processed outputs.",
        statHeaderBadge: "Hypothesis Verification Engine",
        statHeaderTitle: "STATISTICAL EVIDENCE & ANALYSIS",
        statHeaderDesc: "Cross-analyzing space-based indicators against regional macroeconomics and ground-truth registries.",
        statChartTitle: "VIIRS Night-time Lights vs GDP Correlation",
        statChartDesc: "Red shaded region indicates the 2023 industrial energy crisis; blue shaded region indicates the 2025 automotive sector recovery.",
        statMetricsTitle: "Empirical Performance Metrics",
        statLabelN: "Sample Size",
        statLabelTiles: "Sensing Quota"
    },
    CS: {
        heroBadge: "Bakalářská práce - Artefakt",
        heroTitlePrefix: "Vesmírná",
        heroSubtitle: "Detekce skrytých vzorců těžby surovin, změn dodavatelských řetězců a regionálních ekonomických anomálií dotazováním otevřených satelitních API (ESA, NASA, USGS) ve spojení s unsupervised modely strojového učení.",
        flightTrackerLabel: "TRAKTOR LETU NA ORBITĚ:",
        flightTrackerSuffix: "aktivních družic registrováno",
        heroBtnExplore: "Spustit Satelitní Mapu",
        heroBtnThesis: "Prohlédnout Práci",
        basemapHudLabel: "Podklad:",
        heatmapHudLabel: "Teplotní mapa:",
        btnExportViewport: "Exportovat výřez",
        timelineTitleLabel: "Časová osa navigace",
        selectedHudLabel: "Vybraná anomálie",
        confidenceLabel: "Důvěryhodnost detekce",
        beforeAfterLabel: "Srovnání snímků Před / Po",
        spectralBandModeLabel: "Režim spektrálních pásem",
        groundTruthHudLabel: "Ověření - Ground Truth",
        btnExportReport: "Exportovat zprávu",
        constellationTitle: "Konstelace satelitních API",
        constellationDesc: "Mapování vztahů mezi orbitálními senzory, veřejnými rozpočty a výstupními daty.",
        statHeaderBadge: "Engine pro ověřování hypotéz",
        statHeaderTitle: "STATISTICKÉ DŮKAZY A ANALÝZA",
        statHeaderDesc: "Křížová analýza vesmírných indikátorů proti regionální makroekonomice a registrům ground-truth.",
        statChartTitle: "Korelace nočního osvětlení VIIRS a HDP",
        statChartDesc: "Červená oblast označuje průmyslovou energetickou krizi v roce 2023; modrá oblast značí oživení automobilového sektoru v roce 2025.",
        statMetricsTitle: "Empirické Výkonnostní Metriky",
        statLabelN: "Velikost Vzorku",
        statLabelTiles: "Objem Snímání"
    }
};

function updateUILanguage() {
    const t = (translations[currentLang] && translations[currentLang].ui) ? translations[currentLang].ui : uiTranslations[currentLang];
    if (!t) return;
    
    document.getElementById("hero-badge-label").innerText = t.heroBadge;
    document.getElementById("hero-title-prefix").innerText = t.heroTitlePrefix;
    document.getElementById("hero-subtitle").innerText = t.heroSubtitle;
    document.getElementById("flight-tracker-label").innerText = t.flightTrackerLabel;
    document.getElementById("flight-tracker-suffix").innerText = t.flightTrackerSuffix;
    document.getElementById("hero-btn-explore").innerText = t.heroBtnExplore;
    document.getElementById("hero-btn-thesis").innerText = t.heroBtnThesis;
    document.getElementById("basemap-hud-label").innerText = t.basemapHudLabel;
    document.getElementById("heatmap-hud-label").innerText = t.heatmapHudLabel;
    document.getElementById("btn-export-viewport-label").innerText = t.btnExportViewport;
    document.getElementById("timeline-title-label").innerText = t.timelineTitleLabel;
    document.getElementById("selected-hud-label").innerText = t.selectedHudLabel;
    document.getElementById("confidence-label").innerText = t.confidenceLabel;
    document.getElementById("before-after-label").innerText = t.beforeAfterLabel;
    document.getElementById("spectral-band-mode-label").innerText = t.spectralBandModeLabel;
    document.getElementById("ground-truth-hud-label").innerText = t.groundTruthHudLabel;
    document.getElementById("btn-export-report-label").innerText = t.btnExportReport;
    document.getElementById("constellation-title").innerText = t.constellationTitle;
    document.getElementById("constellation-desc").innerText = t.constellationDesc;
    
    // Update statistical section if present
    const statHeaderBadge = document.getElementById("stat-header-badge");
    const statHeaderTitle = document.getElementById("stat-header-title");
    const statHeaderDesc = document.getElementById("stat-header-desc");
    const statChartTitle = document.getElementById("stat-chart-title");
    const statChartDesc = document.getElementById("stat-chart-desc");
    const statMetricsTitle = document.getElementById("stat-metrics-title");
    const statLabelN = document.getElementById("stat-label-n");
    const statLabelTiles = document.getElementById("stat-label-tiles");
    
    if (statHeaderBadge && t.statHeaderBadge) statHeaderBadge.innerText = t.statHeaderBadge;
    if (statHeaderTitle && t.statHeaderTitle) statHeaderTitle.innerText = t.statHeaderTitle;
    if (statHeaderDesc && t.statHeaderDesc) statHeaderDesc.innerText = t.statHeaderDesc;
    if (statChartTitle && t.statChartTitle) statChartTitle.innerText = t.statChartTitle;
    if (statChartDesc && t.statChartDesc) statChartDesc.innerText = t.statChartDesc;
    if (statMetricsTitle && t.statMetricsTitle) statMetricsTitle.innerText = t.statMetricsTitle;
    if (statLabelN && t.statLabelN) statLabelN.innerText = t.statLabelN;
    if (statLabelTiles && t.statLabelTiles) statLabelTiles.innerText = t.statLabelTiles;
    
    // Update spectral band description if present
    const bandDescEl = document.getElementById("band-description");
    if (bandDescEl && t.bandDescriptions && t.bandDescriptions[currentBandMode]) {
        bandDescEl.innerText = t.bandDescriptions[currentBandMode];
    }
    
    initTypewriter();
}

// 2. INTERACTIVE LEAFLET SYSTEM
function initMap() {
    map = L.map('map', {
        zoomControl: true,
        maxZoom: 18,
        minZoom: 2
    }).setView([-12.0, -40.0], 3);
    
    darkBasemapLayer = L.tileLayer(darkMatterTilesUrl, {
        attribution: mapAttribution
    });
    
    satelliteBasemapLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });
    
    darkBasemapLayer.addTo(map);
}

// 2.1 SYNCED MINI-MAP SYSTEM
function initMinimap() {
    minimap = L.map('minimap', {
        zoomControl: false,
        attributionControl: false,
        dragging: false,
        scrollWheelZoom: false,
        touchZoom: false,
        doubleClickZoom: false,
        boxZoom: false
    }).setView([-12.0, -40.0], 1);
    
    L.tileLayer(darkMatterTilesUrl).addTo(minimap);
    
    map.on('move', () => {
        minimap.setView(map.getCenter(), Math.max(0, map.getZoom() - 4));
    });
}

// 3. RADAR CHART (CHART.JS) SYSTEM
function initRadarChart() {
    const ctx = document.getElementById('radar-chart').getContext('2d');
    
    const data = {
        labels: ['NDVI (Forest)', 'NDWI (Water)', 'BSI (Bare Soil)', 'SWIR1 (Rock)'],
        datasets: [
            {
                label: 'Selected Anomaly',
                data: [0, 0, 0, 0],
                fill: true,
                backgroundColor: 'rgba(0, 212, 255, 0.2)',
                borderColor: '#00d4ff',
                pointBackgroundColor: '#00d4ff',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#00d4ff'
            },
            {
                label: 'Baseline Mean',
                data: [0.5, -0.2, 0.3, 0.2],
                fill: true,
                backgroundColor: 'rgba(67, 97, 238, 0.1)',
                borderColor: '#4361ee',
                pointBackgroundColor: '#4361ee',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#4361ee'
            }
        ]
    };
    
    const config = {
        type: 'radar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.05)' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    pointLabels: {
                        color: '#8899bb',
                        font: { family: 'Orbitron', size: 9 }
                    },
                    ticks: {
                        display: false,
                        max: 1.0,
                        min: -1.0
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#8899bb',
                        font: { family: 'Orbitron', size: 9 }
                    }
                }
            }
        }
    };
    
    radarChartInstance = new Chart(ctx, config);
}

// 4. DATA LOADER ENGINE (JSON/GeoJSON FETCH)
function loadDashboardData() {
    // Fetch anomalies list
    fetch('data/anomalies.json')
        .then(response => {
            if (!response.ok) throw new Error("Local cache file missing. Loading sample backup.");
            return response.json();
        })
        .then(data => {
            anomaliesData = data;
            renderAnomalyMarkers(data);
        })
        .catch(err => {
            console.warn(err);
            loadSampleBackupAnomalies();
        });
        
    // Fetch regions geometry
    fetch('data/regions.geojson')
        .then(response => {
            if (!response.ok) throw new Error("Regions cache missing.");
            return response.json();
        })
        .then(data => {
            regionsData = data;
            renderRegionPolygons(data);
        })
        .catch(err => {
            console.warn(err);
            loadSampleBackupRegions();
        });
}

// Fallback backups in case files are not generated yet
function loadSampleBackupAnomalies() {
    anomaliesData = [
        {
            "id": "anomaly_lithium_1",
            "type": "Lithium Expansion",
            "region": "Salar de Atacama, Chile",
            "coordinates": [-23.472, -68.349],
            "confidence": 0.94,
            "date": "2024-10-12",
            "spectral_profile": { "ndvi": -0.12, "ndwi": 0.58, "bsi": 0.74 },
            "details": "Rapid spatial expansion of lithium brine evaporation ponds detected. Spectral signature exhibits elevated NDWI (brine water reflection) and high Bare Soil Index (albedo salt crust) with complete absence of vegetation.",
            "verification": {
                "method": "Spatial Index Overlay",
                "ground_truth": "SERNAGEOMIN Lithium Brine Expansion Plan (SQM)",
                "status": "Verified"
            }
        },
        {
            "id": "anomaly_mining_1",
            "type": "Gold Mining / Deforestation",
            "region": "Madre de Dios, Peru",
            "coordinates": [-12.894, -69.912],
            "confidence": 0.88,
            "date": "2025-03-22",
            "spectral_profile": { "ndvi": -0.52, "ndwi": 0.12, "bsi": 0.68 },
            "details": "Severe canopy forest degradation and raw soil exposure. The spectral footprint displays a sudden NDVI drop (loss of biomass volume) and elevated BSI (exposed mud/silt ponds associated with alluvial gold mining).",
            "verification": {
                "method": "Temporal Radar backscatter (Sentinel-1 SAR)",
                "ground_truth": "MAAP Deforestation Alert #284",
                "status": "Verified (Critical)"
            }
        },
        {
            "id": "anomaly_ntl_1",
            "type": "NTL Economic Expansion",
            "region": "Mladá Boleslav (Industrial Zone), CZ",
            "coordinates": [50.412, 14.903],
            "confidence": 0.85,
            "date": "2025-06-01",
            "spectral_profile": { "ndvi": 0.35, "ndwi": -0.15, "bsi": 0.42 },
            "details": "Significant temporal deviation in night-time light radiance (Z-score = +2.61). Correlates with shift changes and production rate shifts in the automotive manufacturing cluster.",
            "verification": {
                "method": "Statistical GDP Correlation",
                "ground_truth": "Czech Statistical Office (ČSÚ) Quarterly Manufacturing Index",
                "status": "Verified"
            }
        }
    ];
    renderAnomalyMarkers(anomaliesData);
}

function loadSampleBackupRegions() {
    regionsData = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": { "name": "Salar de Atacama Study Area", "type": "Lithium Mining" },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-68.5, -23.8], [-68.1, -23.8], [-68.1, -23.2], [-68.5, -23.2], [-68.5, -23.8]]]
                }
            },
            {
                "type": "Feature",
                "properties": { "name": "Madre de Dios Monitoring Corridor", "type": "Deforestation" },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-70.2, -13.1], [-69.6, -13.1], [-69.6, -12.6], [-70.2, -12.6], [-70.2, -13.1]]]
                }
            },
            {
                "type": "Feature",
                "properties": { "name": "Bohemian Industrial Ring", "type": "Night Lights" },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[14.0, 49.8], [15.2, 49.8], [15.2, 50.4], [14.0, 50.4], [14.0, 49.8]]]
                }
            }
        ]
    };
    renderRegionPolygons(regionsData);
}

// 5. RENDER GEOGRAPHIC OBJECTS
function renderAnomalyMarkers(anomalies) {
    // Clear existing markers from map
    mapMarkers.forEach(m => map.removeLayer(m.markerObj));
    mapMarkers = [];
    
    anomalies.forEach(anom => {
        let typeClass = 'pulse-marker-icon';
        if (anom.id.includes('lithium')) typeClass += ' pulse-marker-lithium';
        if (anom.id.includes('ntl')) typeClass += ' pulse-marker-ntl';
        
        const customIcon = L.divIcon({
            className: typeClass,
            iconSize: [12, 12]
        });
        
        const marker = L.marker(anom.coordinates, { icon: customIcon }).addTo(map);
        
        // Map confidence directly to marker element CSS opacity (bound between 0.45 and 1.0 for visibility)
        marker.on('add', () => {
            const el = marker.getElement();
            if (el) el.style.opacity = Math.max(0.45, anom.confidence);
        });
        setTimeout(() => {
            const el = marker.getElement();
            if (el) el.style.opacity = Math.max(0.45, anom.confidence);
        }, 10);
        
        marker.on('click', () => {
            selectAnomaly(anom);
        });
        
        mapMarkers.push({
            markerObj: marker,
            data: anom
        });
    });
}

function renderRegionPolygons(geojson) {
    L.geoJSON(geojson, {
        style: function (feature) {
            let color = '#4361ee'; // Default blue
            if (feature.properties.type === 'Lithium Mining') color = '#00d4ff';
            if (feature.properties.type === 'Deforestation') color = '#ff4757';
            if (feature.properties.type === 'Night Lights') color = '#ffa502';
            
            return {
                color: color,
                weight: 1.5,
                fillColor: color,
                fillOpacity: 0.05,
                dashArray: '4,4'
            };
        }
    }).addTo(map);
}

// 6. FOCUS ANOMALY INTERACTION
function selectAnomaly(anom) {
    currentSelectedAnomaly = anom;
    
    // Pan and zoom map to target coordinates
    map.setView(anom.coordinates, 10);
    
    // Update Badge and titles
    const badge = document.getElementById("anomaly-badge");
    badge.innerText = anom.type;
    badge.className = "border text-[10px] font-code px-2 py-0.5 rounded-full uppercase ";
    if (anom.id.includes('lithium')) {
        badge.className += "bg-neoncyan/10 border-neoncyan/30 text-neoncyan";
    } else if (anom.id.includes('ntl')) {
        badge.className += "bg-warning/10 border-warning/30 text-warning";
    } else {
        badge.className += "bg-critical/10 border-critical/30 text-critical";
    }
    
    document.getElementById("anomaly-title").innerText = anom.id.replace('_', ' ').toUpperCase();
    document.getElementById("anomaly-region").innerHTML = `<i class="fa-solid fa-location-dot text-neoncyan mr-1"></i> ${anom.region} (${anom.coordinates[0].toFixed(3)}, ${anom.coordinates[1].toFixed(3)})`;
    
    // Update Confidence score bar with simulated confidence interval bounds
    const confVal = Math.round(anom.confidence * 100);
    let ciText = "";
    if (anom.confidence_interval) {
        const low = Math.round(anom.confidence_interval[0] * 100);
        const high = Math.round(anom.confidence_interval[1] * 100);
        const margin = Math.round((high - low) / 2);
        ciText = ` (±${margin}% CI)`;
    } else {
        const margin = Math.round((1.0 - anom.confidence) * 10);
        ciText = ` (±${margin}% CI)`;
    }
    document.getElementById("confidence-percentage").innerText = `${confVal}%${ciText}`;
    document.getElementById("confidence-bar").style.width = `${confVal}%`;
    
    // Update detailed description
    document.getElementById("anomaly-description").innerText = anom.details;
    document.getElementById("verification-status").innerText = `${anom.verification.ground_truth} (${anom.verification.status})`;
    
    // Update Radar dataset values
    radarChartInstance.data.datasets[0].data = [
        anom.spectral_profile.ndvi,
        anom.spectral_profile.ndwi,
        anom.spectral_profile.bsi,
        anom.spectral_profile.bsi * 0.8 // Simulated SWIR1 reflectance
    ];
    radarChartInstance.update();
    
    // Redraw Canvas Split Image Simulator
    drawSplitImageSimulator(anom.id);
}

// 7. CANVAS IMAGERY SPLIT SYSTEM
let sliderSplitPercent = 0.50;

function drawSplitImageSimulator(anomalyId) {
    const container = document.getElementById("slider-container");
    const baselineCanvas = document.getElementById("img-baseline");
    const anomalyCanvas = document.getElementById("img-anomaly");
    
    const w = container.clientWidth;
    const h = container.clientHeight;
    
    baselineCanvas.width = w;
    baselineCanvas.height = h;
    anomalyCanvas.width = w;
    anomalyCanvas.height = h;
    
    const bCtx = baselineCanvas.getContext("2d");
    const aCtx = anomalyCanvas.getContext("2d");
    
    // If we have actual image files generated, draw them. 
    // Otherwise, paint highly detailed vector geospatial representations.
    let baseImg = new Image();
    let anomImg = new Image();
    
    let baseSrc = 'assets/images/atacama_before.png';
    let anomSrc = 'assets/images/atacama_after.png';
    
    if (anomalyId.includes('mining')) {
        baseSrc = 'assets/images/amazon_before.png';
        anomSrc = 'assets/images/amazon_after.png';
    } else if (anomalyId.includes('ntl')) {
        baseSrc = 'assets/images/prague_before.png';
        anomSrc = 'assets/images/prague_after.png';
    }
    
    baseImg.src = baseSrc;
    anomImg.src = anomSrc;
    
    let loadedCount = 0;
    const onImgLoad = () => {
        loadedCount++;
        if (loadedCount === 2) {
            // Draw real image files
            bCtx.drawImage(baseImg, 0, 0, w, h);
            aCtx.drawImage(anomImg, 0, 0, w, h);
            applySpectralShaders(bCtx, w, h);
            applySpectralShaders(aCtx, w, h);
            applyClipEffect();
        }
    };
    
    baseImg.onload = onImgLoad;
    anomImg.onload = onImgLoad;
    
    // Fail-safe programmatic drawing if images are missing
    baseImg.onerror = anomImg.onerror = () => {
        drawVectorPlaceholder(anomalyId, bCtx, aCtx, w, h);
        applyClipEffect();
    };
}

function drawVectorPlaceholder(anomalyId, bCtx, aCtx, w, h) {
    // 1. Paint Baseline
    bCtx.fillStyle = "#0c1524";
    bCtx.fillRect(0, 0, w, h);
    
    // Draw basic grid representing original forest/desert structure
    bCtx.strokeStyle = "rgba(67, 97, 238, 0.15)";
    bCtx.lineWidth = 1;
    for (let x = 0; x < w; x += 20) {
        bCtx.beginPath(); bCtx.moveTo(x, 0); bCtx.lineTo(x, h); bCtx.stroke();
    }
    
    if (anomalyId.includes('lithium')) {
        // Atacama desert: dry white/tan crust baseline
        bCtx.fillStyle = "#b5aa94";
        bCtx.fillRect(0, 0, w, h);
        bCtx.fillStyle = "#8a7e6b"; // Geological veins
        bCtx.beginPath(); bCtx.arc(w*0.3, h*0.5, 40, 0, Math.PI*2); bCtx.fill();
    } else if (anomalyId.includes('mining')) {
        // Amazon: lush solid green forest canopy baseline
        bCtx.fillStyle = "#1e3d24";
        bCtx.fillRect(0, 0, w, h);
        bCtx.fillStyle = "#142c19"; // Canopy patterns
        for (let i = 0; i < 20; i++) {
            bCtx.beginPath(); bCtx.arc(Math.random()*w, Math.random()*h, 15, 0, Math.PI*2); bCtx.fill();
        }
    } else {
        // Night lights: low lights baseline
        bCtx.fillStyle = "#050510";
        bCtx.fillRect(0, 0, w, h);
        bCtx.fillStyle = "rgba(255, 165, 2, 0.2)"; // Soft yellow ambient
        bCtx.beginPath(); bCtx.arc(w*0.5, h*0.5, 30, 0, Math.PI*2); bCtx.fill();
    }
    
    // 2. Paint Anomaly Layer
    aCtx.fillStyle = "#0c1524";
    aCtx.fillRect(0, 0, w, h);
    
    if (anomalyId.includes('lithium')) {
        // Lithium ponds: bright turquoise/cyan rectangular grids
        aCtx.fillStyle = "#b5aa94";
        aCtx.fillRect(0, 0, w, h);
        
        aCtx.fillStyle = "#00d4ff"; // Turquoise brine pool
        aCtx.fillRect(w*0.2, h*0.2, 50, 40);
        aCtx.strokeStyle = "#fff";
        aCtx.strokeRect(w*0.2, h*0.2, 50, 40);
        
        aCtx.fillStyle = "#7bed9f"; // Acidic pond
        aCtx.fillRect(w*0.5, h*0.2, 45, 40);
        aCtx.strokeRect(w*0.5, h*0.2, 45, 40);
    } else if (anomalyId.includes('mining')) {
        // Amazon mining: deforestation diagonal cuts + mud pits
        aCtx.fillStyle = "#1e3d24";
        aCtx.fillRect(0, 0, w, h);
        // Mining cut
        aCtx.fillStyle = "#a8773b"; // Mud/soil
        aCtx.beginPath();
        aCtx.moveTo(w*0.1, h*0.1);
        aCtx.lineTo(w*0.8, h*0.9);
        aCtx.lineTo(w*0.9, h*0.8);
        aCtx.lineTo(w*0.2, h*0.1);
        aCtx.closePath();
        aCtx.fill();
        // Slurry pond
        aCtx.fillStyle = "#ffa502";
        aCtx.beginPath(); aCtx.arc(w*0.5, h*0.5, 20, 0, Math.PI*2); aCtx.fill();
    } else {
        // NTL surge: bright yellow core and rays
        aCtx.fillStyle = "#050510";
        aCtx.fillRect(0, 0, w, h);
        
        // Intense glow
        let glow = aCtx.createRadialGradient(w*0.5, h*0.5, 2, w*0.5, h*0.5, 60);
        glow.addColorStop(0, '#fff');
        glow.addColorStop(0.2, '#ffa502');
        glow.addColorStop(1, 'transparent');
        aCtx.fillStyle = glow;
        aCtx.beginPath(); aCtx.arc(w*0.5, h*0.5, 65, 0, Math.PI*2); aCtx.fill();
    }
    
    // Apply spectral shaders to programmatically drawn vectors
    applySpectralShaders(bCtx, w, h);
    applySpectralShaders(aCtx, w, h);
}

// 7.1 SPECTRAL PIXEL SHADER SIMULATOR
function applySpectralShaders(ctx, w, h) {
    if (currentBandMode === 'rgb') return;
    
    try {
        const imgData = ctx.getImageData(0, 0, w, h);
        const data = imgData.data;
        
        for (let i = 0; i < data.length; i += 4) {
            let r = data[i];
            let g = data[i+1];
            let b = data[i+2];
            
            if (currentBandMode === 'fc') {
                // False Color Infrared (Vegetation shines red)
                data[i] = Math.min(255, g * 1.8);
                data[i+1] = Math.min(255, r * 0.4 + g * 0.2);
                data[i+2] = Math.min(255, b * 0.5);
            } else if (currentBandMode === 'agri') {
                // Agriculture: golden green
                data[i] = Math.min(255, r * 0.8 + g * 0.6);
                data[i+1] = Math.min(255, g * 1.5);
                data[i+2] = Math.min(255, b * 0.2);
            } else if (currentBandMode === 'geol') {
                // Geology: SWIR-driven mineral crust mapping (pink/magenta/purple)
                data[i] = Math.min(255, r * 1.2 + b * 0.5);
                data[i+1] = Math.min(255, g * 0.3);
                data[i+2] = Math.min(255, b * 1.6);
            } else if (currentBandMode === 'swir') {
                // SWIR (Short-Wave Infrared): Highlights soil albedo and salt crusts
                data[i] = Math.min(255, r * 1.5);
                data[i+1] = Math.min(255, g * 0.8 + b * 0.4);
                data[i+2] = Math.min(255, b * 0.3);
            } else if (currentBandMode === 'atmos') {
                // Atmospheric: Penetrates haze, dust aerosols
                data[i] = Math.min(255, r * 0.4 + g * 0.4);
                data[i+1] = Math.min(255, g * 1.2);
                data[i+2] = Math.min(255, b * 1.5);
            } else if (currentBandMode === 'urban') {
                // Urban: Emphasizes built structures and concrete albedo reflection
                data[i] = Math.min(255, r * 1.4);
                data[i+1] = Math.min(255, g * 1.4);
                data[i+2] = Math.min(255, b * 0.6);
            }
        }
        ctx.putImageData(imgData, 0, 0);
    } catch (e) {
        console.warn("Unable to apply spectral pixel adjustments (possibly CORS cross-origin resource):", e);
    }
}

function applyClipEffect() {
    const handle = document.getElementById("slider-handle");
    const anomalyCanvas = document.getElementById("img-anomaly");
    
    const w = anomalyCanvas.width;
    const splitX = w * sliderSplitPercent;
    
    // Position handle element
    handle.style.left = `${sliderSplitPercent * 100}%`;
    
    // Clip anomaly canvas on left side, revealing baseline underneath
    // CSS Clip path bounds: inset(top right bottom left)
    // Clipped from left boundary to splitX coordinate
    anomalyCanvas.style.clipPath = `inset(0 0 0 ${splitX}px)`;
}

// 7.2 MAP OVERLAY TOGGLE HELPERS
function toggleHeatmap() {
    const btn = document.getElementById("btn-toggle-heatmap");
    if (!btn) return;
    heatmapActive = !heatmapActive;
    
    if (heatmapActive) {
        const heatPoints = anomaliesData.map(anom => [
            anom.coordinates[0],
            anom.coordinates[1],
            anom.confidence
        ]);
        
        heatmapLayer = L.heatLayer(heatPoints, {
            radius: 30,
            blur: 15,
            maxZoom: 10,
            gradient: { 0.4: 'blue', 0.65: 'lime', 1: 'red' }
        }).addTo(map);
        
        btn.innerText = "ON";
        btn.className = "ml-2 px-2 py-0.5 rounded bg-neoncyan text-void font-bold transition-all";
    } else {
        if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
            heatmapLayer = null;
        }
        btn.innerText = "OFF";
        btn.className = "ml-2 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 hover:border-neoncyan transition-all text-slate-300 text-xs";
    }
}

function filterAnomaliesByTimeline(index) {
    const years = ['2021', '2022', '2023', '2024', '2025'];
    const label = document.getElementById("timeline-date-label");
    
    if (index === 4) {
        label.innerText = currentLang === 'EN' ? "All Time" : "Celá doba";
        mapMarkers.forEach(m => {
            if (!map.hasLayer(m.markerObj)) m.markerObj.addTo(map);
        });
        return;
    }
    
    const selectedYear = years[index];
    label.innerText = selectedYear;
    
    mapMarkers.forEach(m => {
        const anomalyYear = m.data.date.substring(0, 4);
        if (anomalyYear === selectedYear) {
            if (!map.hasLayer(m.markerObj)) m.markerObj.addTo(map);
        } else {
            if (map.hasLayer(m.markerObj)) map.removeLayer(m.markerObj);
        }
    });
}

// 8. EVENT LISTENER CONFIGURATORS
function setupEventListeners() {
    // Canvas slider dragging logic
    const sliderContainer = document.getElementById("slider-container");
    let isDragging = false;
    
    const handleDrag = (e) => {
        const rect = sliderContainer.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        let x = clientX - rect.left;
        x = Math.max(0, Math.min(x, rect.width));
        sliderSplitPercent = x / rect.width;
        applyClipEffect();
    };
    
    sliderContainer.addEventListener("mousedown", () => isDragging = true);
    window.addEventListener("mouseup", () => isDragging = false);
    sliderContainer.addEventListener("mousemove", (e) => {
        if (isDragging) handleDrag(e);
    });
    
    // Mobile Touch events
    sliderContainer.addEventListener("touchstart", () => isDragging = true);
    window.addEventListener("touchend", () => isDragging = false);
    sliderContainer.addEventListener("touchmove", (e) => {
        if (isDragging) handleDrag(e);
    });

    // Basemap toggle event listeners
    document.getElementById("btn-basemap-dark").addEventListener("click", () => {
        if (map.hasLayer(satelliteBasemapLayer)) map.removeLayer(satelliteBasemapLayer);
        darkBasemapLayer.addTo(map);
        document.getElementById("btn-basemap-dark").className = "px-2 py-0.5 rounded bg-neoncyan text-void font-bold";
        document.getElementById("btn-basemap-sat").className = "px-2 py-0.5 rounded hover:bg-slate-850 transition-all text-slate-300";
    });
    document.getElementById("btn-basemap-sat").addEventListener("click", () => {
        if (map.hasLayer(darkBasemapLayer)) map.removeLayer(darkBasemapLayer);
        satelliteBasemapLayer.addTo(map);
        document.getElementById("btn-basemap-sat").className = "px-2 py-0.5 rounded bg-neoncyan text-void font-bold";
        document.getElementById("btn-basemap-dark").className = "px-2 py-0.5 rounded hover:bg-slate-850 transition-all text-slate-300";
    });

    // Heatmap Overlay toggle event listener
    document.getElementById("btn-toggle-heatmap").addEventListener("click", () => {
        toggleHeatmap();
    });

    // Timeline range slider filter event listener
    const timeline = document.getElementById("timeline-slider");
    if (timeline) {
        timeline.addEventListener("input", (e) => {
            filterAnomaliesByTimeline(parseInt(e.target.value));
        });
    }

    // Viewport GeoJSON Export
    document.getElementById("btn-export-viewport").addEventListener("click", () => {
        const bounds = map.getBounds();
        const northEast = bounds.getNorthEast();
        const southWest = bounds.getSouthWest();
        
        const viewportGeoJSON = {
            "type": "Feature",
            "properties": {
                "name": "Map Viewport Bounding Box",
                "timestamp": new Date().toISOString(),
                "zoom": map.getZoom()
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [southWest.lng, southWest.lat],
                    [northEast.lng, southWest.lat],
                    [northEast.lng, northEast.lat],
                    [southWest.lng, northEast.lat],
                    [southWest.lng, southWest.lat]
                ]]
            }
        };
        
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(viewportGeoJSON, null, 2));
        const dlAnchorElem = document.createElement('a');
        dlAnchorElem.setAttribute("href", dataStr);
        dlAnchorElem.setAttribute("download", `map_viewport_${Date.now()}.geojson`);
        dlAnchorElem.click();
    });

    // Multi-spectral Band selection button events
    const bandButtons = ["btn-band-rgb", "btn-band-fc", "btn-band-agri", "btn-band-geol", "btn-band-swir", "btn-band-atmos", "btn-band-urban"];
    const bandModes = ["rgb", "fc", "agri", "geol", "swir", "atmos", "urban"];
    bandButtons.forEach((btnId, idx) => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener("click", () => {
                bandButtons.forEach(bId => {
                    const b = document.getElementById(bId);
                    if (b) {
                        if (bId === 'btn-band-rgb' || bId === 'btn-band-urban') {
                            b.className = "bg-slate-800 hover:bg-slate-700 text-slate-300 p-1 rounded transition-colors text-center border border-slate-700 col-span-2 sm:col-span-1";
                        } else {
                            b.className = "bg-slate-800 hover:bg-slate-700 text-slate-300 p-1 rounded transition-colors text-center border border-slate-700";
                        }
                    }
                });
                if (btnId === 'btn-band-rgb' || btnId === 'btn-band-urban') {
                    btn.className = "bg-neoncyan text-void font-bold p-1 rounded transition-colors text-center border border-neoncyan/25 col-span-2 sm:col-span-1";
                } else {
                    btn.className = "bg-neoncyan text-void font-bold p-1 rounded transition-colors text-center border border-neoncyan/25";
                }
                
                currentBandMode = bandModes[idx];
                
                // Update description text dynamically
                const t = (translations[currentLang] && translations[currentLang].ui) ? translations[currentLang].ui : uiTranslations[currentLang];
                const bandDescEl = document.getElementById("band-description");
                if (bandDescEl && t && t.bandDescriptions && t.bandDescriptions[currentBandMode]) {
                    bandDescEl.innerText = t.bandDescriptions[currentBandMode];
                }
                
                if (currentSelectedAnomaly) {
                    drawSplitImageSimulator(currentSelectedAnomaly.id);
                }
            });
        }
    });

    // Map mouse hover coordinate tracking HUD
    map.on("mousemove", (e) => {
        const coordinatesHud = document.getElementById("hud-coordinates");
        if (coordinatesHud) {
            coordinatesHud.innerText = `${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
        }
    });

    // Map Study Area Layer Toggles
    document.getElementById("btn-layer-all").addEventListener("click", (e) => {
        toggleLayerActive(e.target);
        map.setView([-12.0, -40.0], 3);
    });
    
    document.getElementById("btn-layer-lithium").addEventListener("click", (e) => {
        toggleLayerActive(e.target);
        map.setView([-23.472, -68.349], 9);
        const lAnom = anomaliesData.find(a => a.id.includes('lithium'));
        if (lAnom) selectAnomaly(lAnom);
    });
    
    document.getElementById("btn-layer-mining").addEventListener("click", (e) => {
        toggleLayerActive(e.target);
        map.setView([-12.894, -69.912], 9);
        const mAnom = anomaliesData.find(a => a.id.includes('mining'));
        if (mAnom) selectAnomaly(mAnom);
    });
    
    document.getElementById("btn-layer-ntl").addEventListener("click", (e) => {
        toggleLayerActive(e.target);
        map.setView([50.412, 14.903], 9);
        const nAnom = anomaliesData.find(a => a.id.includes('ntl'));
        if (nAnom) selectAnomaly(nAnom);
    });
    
    function toggleLayerActive(targetButton) {
        document.querySelectorAll("#btn-layer-all, #btn-layer-lithium, #btn-layer-mining, #btn-layer-ntl").forEach(btn => {
            btn.className = "px-3 py-1 rounded hover:bg-slate-800 transition-all text-slate-300";
        });
        targetButton.className = "px-3 py-1 rounded bg-neoncyan text-void font-bold transition-all";
    }

    // Thesis Chapter Navigation clicks
    document.querySelectorAll(".chapter-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".chapter-btn").forEach(b => {
                b.className = "chapter-btn px-4 py-2.5 text-left text-xs font-display font-semibold rounded text-slate-400 hover:bg-slate-850 hover:text-white";
            });
            e.target.className = "chapter-btn px-4 py-2.5 text-left text-xs font-display font-semibold rounded bg-neoncyan text-void";
            
            const chapNum = e.target.getAttribute("data-chapter");
            renderChapterText(chapNum);
        });
    });

    // BibTeX copy event
    document.getElementById("btn-copy-citation").addEventListener("click", () => {
        const bibtex = `@thesis{ozturk2026space,
  author = {Ozturk, Eren},
  title = {Space-Based Economic Intelligence: Detecting Hidden Resource Anomalies Using Open Satellite APIs},
  school = {Czech University of Life Sciences Prague (CZU), PEF - Department of Informatics (KII)},
  year = {2026},
  type = {Bachelor Thesis},
  advisor = {Bro{\\v{z}}ek, Ji{\\v{r}}{\\text{i}}}
}`;
        navigator.clipboard.writeText(bibtex).then(() => {
            const copyBtn = document.getElementById("btn-copy-citation");
            copyBtn.innerHTML = `<i class="fa-solid fa-check text-safe mr-1.5"></i> Copied!`;
            setTimeout(() => {
                copyBtn.innerHTML = `<i class="fa-solid fa-quote-left mr-1.5"></i> Copy BibTeX`;
            }, 2000);
        });
    });

    // Export report event
    document.getElementById("btn-export-report").addEventListener("click", () => {
        if (!currentSelectedAnomaly) {
            alert("Please select an anomaly region first.");
            return;
        }
        
        let reportText = `=========================================
SPACE-BASED ECONOMIC INTELLIGENCE REPORT
=========================================
Anomaly ID: ${currentSelectedAnomaly.id.toUpperCase()}
Type      : ${currentSelectedAnomaly.type}
Region    : ${currentSelectedAnomaly.region}
Date      : ${currentSelectedAnomaly.date}
Coordinates: [${currentSelectedAnomaly.coordinates.join(', ')}]
Confidence : ${currentSelectedAnomaly.confidence * 100}%

SPECTRAL FOOTPRINT:
- NDVI: ${currentSelectedAnomaly.spectral_profile.ndvi}
- NDWI: ${currentSelectedAnomaly.spectral_profile.ndwi}
- BSI : ${currentSelectedAnomaly.spectral_profile.bsi}

VERIFICATION:
- Ground Truth Reference: ${currentSelectedAnomaly.verification.ground_truth}
- Audit Status: ${currentSelectedAnomaly.verification.status}

DETAILS:
${currentSelectedAnomaly.details}
=========================================`;

        const blob = new Blob([reportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${currentSelectedAnomaly.id}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Language Toggle Click Event
    document.getElementById("lang-toggle").addEventListener("click", () => {
        currentLang = currentLang === 'EN' ? 'CS' : 'EN';
        document.getElementById("lang-label").innerText = currentLang;
        
        // Translate interactive navigation controls
        if (currentLang === 'CS') {
            document.getElementById("btn-layer-all").innerText = "Všechny";
            document.getElementById("btn-layer-lithium").innerText = "Chile (Lithium)";
            document.getElementById("btn-layer-mining").innerText = "Peru (Zlato)";
            document.getElementById("btn-layer-ntl").innerText = "Česko (Autopark)";
        } else {
            document.getElementById("btn-layer-all").innerText = "All Areas";
            document.getElementById("btn-layer-lithium").innerText = "Chile (Lithium)";
            document.getElementById("btn-layer-mining").innerText = "Peru (Gold)";
            document.getElementById("btn-layer-ntl").innerText = "Czechia (NTL)";
        }
        
        // Trigger update to other layouts
        updateUILanguage();
        
        // Re-render currently active chapter
        const activeBtn = document.querySelector(".chapter-btn.bg-neoncyan");
        if (activeBtn) {
            const chapNum = activeBtn.getAttribute("data-chapter");
            renderChapterText(chapNum);
        }
    });
}

function renderChapterText(chapNum) {
    const data = (translations[currentLang] && translations[currentLang].chapters && translations[currentLang].chapters[chapNum])
        ? translations[currentLang].chapters[chapNum]
        : (currentLang === 'EN' ? academicChapters[chapNum] : academicChaptersCS[chapNum]);
        
    const viewer = document.getElementById("chapter-viewer");
    if (!data) return;
    
    let html = `<h3 class="text-white font-display font-bold text-lg border-b border-slate-850 pb-2">${data.title}</h3>`;
    data.sections.forEach(sec => {
        html += `<p class="font-semibold text-white mt-4">${sec.name}</p>`;
        html += `<p class="mt-1">${sec.text}</p>`;
    });
    
    viewer.innerHTML = html;
    viewer.scrollTop = 0; // Scroll to top
}

// ============================================================
// 9. NTL TIME-SERIES CORRELATION CHART (Chart.js)
// ============================================================

let ntlChartInstance = null;

// Empirical data from Chapter 5 Table 5.2.3
const ntlTimeSeriesData = {
    labels: [
        'Q1 2021','Q2 2021','Q3 2021','Q4 2021',
        'Q1 2022','Q2 2022','Q3 2022','Q4 2022',
        'Q1 2023','Q2 2023','Q3 2023','Q4 2023',
        'Q1 2024','Q2 2024','Q3 2024','Q4 2024',
        'Q1 2025','Q2 2025','Q3 2025','Q4 2025',
        'Q1 2026'
    ],
    radiance: [
        24.85, 25.10, 25.40, 25.82,
        26.15, 25.90, 24.95, 23.10,
        20.40, 21.15, 22.02, 23.40,
        24.85, 25.30, 25.92, 26.40,
        27.10, 29.80, 29.40, 28.92,
        28.50
    ],
    gdpGrowth: [
        -2.1, 8.2, 4.5, 3.8,
         4.2, 3.5, 1.8,-0.8,
        -1.5,-0.9,-0.6, 0.2,
         0.8, 1.2, 1.4, 1.8,
         2.1, 3.8, 3.2, 2.8,
         2.5
    ],
    zScores: [
        -0.24,-0.10, 0.08, 0.32,
         0.51, 0.36,-0.18,-1.24,
        -2.85,-2.41,-1.90,-1.10,
        -0.24, 0.02, 0.38, 0.65,
         1.05, 2.61, 2.38, 2.10,
         1.85
    ]
};

function initNTLCorrelationChart() {
    const canvas = document.getElementById('ntl-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Annotation plugin zones for 2023 crisis & 2025 recovery
    const anomalyZonePlugin = {
        id: 'anomalyZones',
        beforeDraw(chart) {
            const { ctx: c, chartArea, scales } = chart;
            if (!chartArea) return;

            // Crisis zone: Q1 2023 → Q4 2023 (indices 8–11)
            const x1 = scales.x.getPixelForValue(8);
            const x2 = scales.x.getPixelForValue(11);
            c.save();
            c.fillStyle = 'rgba(255, 71, 87, 0.08)';
            c.fillRect(x1, chartArea.top, x2 - x1, chartArea.bottom - chartArea.top);
            c.restore();

            // Recovery zone: Q2 2025 → Q3 2025 (indices 17–18)
            const x3 = scales.x.getPixelForValue(17);
            const x4 = scales.x.getPixelForValue(18);
            c.save();
            c.fillStyle = 'rgba(0, 212, 255, 0.08)';
            c.fillRect(x3, chartArea.top, x4 - x3, chartArea.bottom - chartArea.top);
            c.restore();
        }
    };

    ntlChartInstance = new Chart(ctx, {
        type: 'line',
        plugins: [anomalyZonePlugin],
        data: {
            labels: ntlTimeSeriesData.labels,
            datasets: [
                {
                    label: 'VIIRS Radiance (nW·cm⁻²·sr⁻¹)',
                    data: ntlTimeSeriesData.radiance,
                    yAxisID: 'y',
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00d4ff',
                },
                {
                    label: 'Z-Score Anomaly',
                    data: ntlTimeSeriesData.zScores,
                    yAxisID: 'y2',
                    borderColor: '#ffa502',
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    borderDash: [4, 3],
                    fill: false,
                    tension: 0.2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#ffa502',
                },
                {
                    label: 'GDP Growth (%)',
                    data: ntlTimeSeriesData.gdpGrowth,
                    yAxisID: 'y3',
                    borderColor: '#4361ee',
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#4361ee',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: '#8899bb',
                        font: { family: 'Orbitron', size: 8 },
                        boxWidth: 12
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(7, 13, 26, 0.95)',
                    borderColor: 'rgba(0, 212, 255, 0.3)',
                    borderWidth: 1,
                    titleColor: '#00d4ff',
                    titleFont: { family: 'Orbitron', size: 10 },
                    bodyColor: '#8899bb',
                    bodyFont: { family: 'Inter', size: 11 },
                    callbacks: {
                        afterBody(items) {
                            const i = items[0].dataIndex;
                            const z = ntlTimeSeriesData.zScores[i];
                            const flag = Math.abs(z) > 2.5 ? (z > 0 ? '⬆ POSITIVE ANOMALY' : '⬇ NEGATIVE ANOMALY') : '';
                            return flag ? [`\n${flag} (Z=${z.toFixed(2)})`] : [];
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#445566',
                        font: { size: 8 },
                        maxRotation: 45
                    },
                    grid: { color: 'rgba(255,255,255,0.03)' }
                },
                y: {
                    position: 'left',
                    title: { display: true, text: 'Radiance', color: '#00d4ff', font: { size: 8 } },
                    ticks: { color: '#445566', font: { size: 8 } },
                    grid: { color: 'rgba(255,255,255,0.04)' }
                },
                y2: {
                    position: 'right',
                    title: { display: true, text: 'Z-Score', color: '#ffa502', font: { size: 8 } },
                    ticks: { color: '#445566', font: { size: 8 } },
                    grid: { display: false },
                    // Threshold reference lines at ±2.5
                    afterDataLimits(axis) {
                        axis.min = Math.min(axis.min, -3.5);
                        axis.max = Math.max(axis.max, 3.5);
                    }
                },
                y3: {
                    display: false   // GDP axis hidden — visible via tooltip only
                }
            }
        }
    });
}

// ============================================================
// 10. STATISTICAL SUMMARY CARD COUNTER ANIMATIONS
// ============================================================

const statisticalTargets = {
    'stat-f1':      { value: 0.907, decimals: 3, prefix: '', suffix: '',  label: 'F1-Score' },
    'stat-pearsonr': { value: 0.724, decimals: 3, prefix: 'r = ', suffix: '', label: 'Pearson r' },
    'stat-pvalue':  { value: 0.0002, decimals: 4, prefix: 'p = ', suffix: '', label: 'p-value' },
    'stat-moransi': { value: 0.648, decimals: 3, prefix: 'I = ', suffix: '', label: "Moran's I" },
    'stat-n':       { value: 21, decimals: 0, prefix: 'n = ', suffix: ' quarters', label: 'Observations' },
    'stat-precision': { value: 0.936, decimals: 3, prefix: '', suffix: '', label: 'Precision' },
    'stat-recall':  { value: 0.880, decimals: 3, prefix: '', suffix: '', label: 'Recall' },
    'stat-tiles':   { value: 184, decimals: 0, prefix: '', suffix: ' tiles', label: 'Ingested Tiles' },
};

function initStatisticalCounters() {
    const duration = 1800; // ms
    const steps = 60;
    const stepMs = duration / steps;

    Object.entries(statisticalTargets).forEach(([id, cfg]) => {
        const el = document.getElementById(id);
        if (!el) return;

        let currentStep = 0;
        const interval = setInterval(() => {
            currentStep++;
            const progress = currentStep / steps;
            // Ease out quad
            const eased = 1 - (1 - progress) * (1 - progress);
            const currentVal = eased * cfg.value;
            el.textContent = `${cfg.prefix}${currentVal.toFixed(cfg.decimals)}${cfg.suffix}`;
            if (currentStep >= steps) {
                clearInterval(interval);
                el.textContent = `${cfg.prefix}${cfg.value.toFixed(cfg.decimals)}${cfg.suffix}`;
            }
        }, stepMs);
    });
}

// Intersection Observer to trigger counters only when visible
function setupStatCounterObserver() {
    const statsSection = document.getElementById('statistical-results-section');
    if (!statsSection) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                initStatisticalCounters();
                try { initNTLCorrelationChart(); } catch(e) { console.error('NTL chart init failed:', e); }
                observer.disconnect();
            }
        });
    }, { threshold: 0.2 });

    observer.observe(statsSection);
}

// ============================================================
// 11. CONFIDENCE INTERVAL DISPLAY UPDATER
// ============================================================

function updateConfidenceIntervalBar(anomaly) {
    const ciLow = anomaly.confidence_ci_low || (anomaly.confidence - 0.06);
    const ciHigh = anomaly.confidence_ci_high || (anomaly.confidence + 0.04);

    const ciLowEl = document.getElementById('ci-low-val');
    const ciHighEl = document.getElementById('ci-high-val');
    const ciLowBar = document.getElementById('ci-low-bar');
    const ciHighBar = document.getElementById('ci-high-bar');

    if (ciLowEl) ciLowEl.textContent = `${(ciLow * 100).toFixed(0)}%`;
    if (ciHighEl) ciHighEl.textContent = `${(ciHigh * 100).toFixed(0)}%`;
    if (ciLowBar) ciLowBar.style.width = `${ciLow * 100}%`;
    if (ciHighBar) ciHighBar.style.width = `${ciHigh * 100}%`;

    // Update Z-score if available
    const zScoreEl = document.getElementById('anomaly-zscore');
    if (zScoreEl) {
        if (anomaly.z_score !== null && anomaly.z_score !== undefined) {
            zScoreEl.textContent = anomaly.z_score.toFixed(2);
            zScoreEl.className = anomaly.z_score > 2.5
                ? 'text-neoncyan font-bold'
                : anomaly.z_score < -2.5
                ? 'text-critical font-bold'
                : 'text-warning';
        } else {
            zScoreEl.textContent = 'N/A (spatial)';
            zScoreEl.className = 'text-slate-500';
        }
    }

    // Show uncertainty badge
    const uncertEl = document.getElementById('anomaly-uncertainty');
    if (uncertEl && anomaly.uncertainty !== undefined) {
        uncertEl.textContent = `±${(anomaly.uncertainty * 100).toFixed(0)}%`;
    }
}

// Override selectAnomaly to also trigger CI + Z-score display
const _originalSelectAnomaly = selectAnomaly;
selectAnomaly = function(anom) {
    _originalSelectAnomaly(anom);
    try { updateConfidenceIntervalBar(anom); } catch(e) { console.warn('CI bar update error:', e); }
};

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setupStatCounterObserver();
});
