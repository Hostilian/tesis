// Version 6 globe view of the Portugal Sentinel-2 case study.
// Every number shown is read at run time from docs/case-study/data/<case>/*.json.
// Nothing here is hard-coded data; the only constants are layer styling and camera positions.
"use strict";
(() => {
  const DATA = "case-study/data/";
  const CASE_ORDER = ["alqueva_olive", "neves_corvo_mine"];
  const SHORT = { alqueva_olive: "Alqueva irrigation area", neves_corvo_mine: "Neves-Corvo mine" };
  const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  const PORTUGAL = { center: [-8.1, 39.4], zoom: 5.4, pitch: 0, bearing: 0 };
  const GLOBE = { center: [-22, 33], zoom: 1.35, pitch: 0, bearing: 0 };
  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const reduced = () => motionQuery.matches;

  const $ = id => document.getElementById(id);
  const fmt = (x, d = 0) => (x === null || x === undefined || Number.isNaN(Number(x))) ? "–" : Number(x).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (x, d = 1) => (x === null || x === undefined) ? "–" : fmt(100 * x, d) + " %";
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const STATUS = {
    public_observation: ["b-obs", "public observation"],
    observation_derived_result: ["b-der", "observation-derived result"],
    unverified_interpretation: ["b-int", "unverified interpretation"],
    synthetic_demonstration: ["b-syn", "synthetic demonstration"],
  };
  const badge = s => STATUS[s] ? `<span class="badge ${STATUS[s][0]}">${STATUS[s][1]}</span>` : "";
  const day = iso => String(iso || "").slice(0, 10);

  const state = {
    index: null, results: {}, robustness: {}, refcos: {}, independent: {},
    caseId: null, opacity: 0.85, tour: 0, markers: {},
    layers: { after: true, before: false, delta: false, change: true, patches: false, cos: false },
    loadedVectors: {},
  };

  async function getJSON(path, optional = false) {
    const r = await fetch(path, { cache: "no-cache" });
    if (!r.ok) { if (optional) return null; throw new Error(`${path}: HTTP ${r.status}`); }
    return r.json();
  }

  // ---------- Map ----------
  const map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      projection: { type: "globe" },
      sky: {
        "sky-color": "#0b2a44", "horizon-color": "#3d7fa8", "fog-color": "#0b1a26",
        "sky-horizon-blend": 0.6, "horizon-fog-blend": 0.6, "fog-ground-blend": 0.9,
        "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 6, 0.6, 9, 0],
      },
      sources: {
        esri: {
          type: "raster", tiles: [ESRI], tileSize: 256, maxzoom: 19,
          attribution: "Basemap © Esri, Maxar, Earthstar Geographics",
        },
      },
      layers: [
        { id: "ground", type: "background", paint: { "background-color": "#061019" } },
        { id: "esri", type: "raster", source: "esri", paint: { "raster-fade-duration": 0 } },
      ],
    },
    center: GLOBE.center, zoom: GLOBE.zoom, maxZoom: 17.5,
    attributionControl: false, fadeDuration: 0,
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
  if (maplibregl.GlobeControl) map.addControl(new maplibregl.GlobeControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
  map.addControl(new maplibregl.AttributionControl({
    compact: false,
    customAttribution: "Overlays: contains modified Copernicus Sentinel data 2018, 2025 · COS © DGT (CC-BY) · DMS readout: God's Eye View (MIT)",
  }), "bottom-right");

  const mapLoaded = new Promise(res => map.on("load", res));
  const empty = { type: "FeatureCollection", features: [] };
  const RASTERS = ["after", "before", "delta", "change"];
  const FILES = { after: "overlay_after.jpg", before: "overlay_before.jpg", delta: "overlay_delta.png", change: "overlay_change.png" };

  // [south, west, north, east] from results.json -> MapLibre corner list (TL, TR, BR, BL as [lon, lat]).
  const corners = b => [[b[1], b[2]], [b[3], b[2]], [b[3], b[0]], [b[1], b[0]]];
  const bboxPolygon = b => ({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]] } });

  function vis(on) { return on ? "visible" : "none"; }

  function addCaseLayers(caseId) {
    const r = state.results[caseId];
    const ob = r.web.overlay_bounds_latlng;
    const base = DATA + caseId + "/";
    const lg = r.web.legend;
    RASTERS.forEach(k => {
      map.addSource(`${caseId}-${k}`, { type: "image", url: base + FILES[k], coordinates: corners(ob[k]) });
      map.addLayer({ id: `${caseId}-${k}`, type: "raster", source: `${caseId}-${k}`,
        layout: { visibility: vis(state.layers[k]) },
        paint: { "raster-opacity": state.opacity, "raster-fade-duration": 0 } }, "aoi-line");
    });
    map.addSource(`${caseId}-cos`, { type: "geojson", data: empty });
    map.addLayer({ id: `${caseId}-cos`, type: "line", source: `${caseId}-cos`, layout: { visibility: vis(state.layers.cos) },
      paint: { "line-color": ["case", ["==", ["slice", ["get", "cos25v1_n4_c"], 0, 4], "1.6."], "#ffcc00", "#b8f2b8"], "line-width": 1.4, "line-dasharray": [2, 2], "line-opacity": state.opacity } }, "aoi-line");
    map.addSource(`${caseId}-patches`, { type: "geojson", data: empty });
    const pcolor = ["case", ["==", ["get", "change_class"], "increase"], lg.increase.color, lg.decrease.color];
    map.addLayer({ id: `${caseId}-patches-fill`, type: "fill", source: `${caseId}-patches`, layout: { visibility: vis(state.layers.patches) },
      paint: { "fill-color": pcolor, "fill-opacity": 0.3 * state.opacity } }, "aoi-line");
    map.addLayer({ id: `${caseId}-patches-line`, type: "line", source: `${caseId}-patches`, layout: { visibility: vis(state.layers.patches) },
      paint: { "line-color": pcolor, "line-width": 1.2, "line-opacity": state.opacity } }, "aoi-line");
    map.on("click", `${caseId}-patches-fill`, e => patchPopup(caseId, e));
    map.on("mouseenter", `${caseId}-patches-fill`, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", `${caseId}-patches-fill`, () => { map.getCanvas().style.cursor = ""; });
  }

  function patchPopup(caseId, e) {
    const f = e.features && e.features[0];
    if (!f) return;
    const p = f.properties, r = state.results[caseId];
    let html = `<b>${esc(p.change_class)} patch</b> ${badge(p.data_status)}<br>Area: ${fmt(p.area_ha, 1)} ha<br>Mean ${esc(r.web.index_label)} difference: ${fmt(p.mean_delta, 3)}`;
    if (p.seasonal_amplitude !== undefined && p.seasonal_amplitude !== null) html += `<br>After-year Aug − May NDVI: ${fmt(p.seasonal_amplitude, 3)} ${badge("unverified_interpretation")}`;
    html += `<br><span class="muted">Cause not verified.</span>`;
    new maplibregl.Popup({ maxWidth: "280px" }).setLngLat(e.lngLat).setHTML(html).addTo(map);
  }

  // COS 2025: keep permanent crops (2.2.x) and mines/quarries (1.6.x), as on the 2D case-study page.
  const cosPick = f => { const c = f.properties.cos25v1_n4_c || ""; return c.startsWith("2.2.") || c.startsWith("1.6."); };

  async function ensureVectors(kind) {
    const jobs = CASE_ORDER.filter(c => state.results[c] && !state.loadedVectors[`${c}-${kind}`]).map(async c => {
      state.loadedVectors[`${c}-${kind}`] = true;
      const file = kind === "patches" ? "patches.geojson" : "reference_cos2025v1.geojson";
      const gj = await getJSON(DATA + c + "/" + file, true);
      if (!gj) { state.loadedVectors[`${c}-${kind}`] = false; return; }
      const data = kind === "cos" ? { type: "FeatureCollection", features: gj.features.filter(cosPick) } : gj;
      map.getSource(`${c}-${kind}`).setData(data);
    });
    await Promise.all(jobs);
  }

  function layerIds(kind) {
    return CASE_ORDER.filter(c => state.results[c]).flatMap(c => kind === "patches" ? [`${c}-patches-fill`, `${c}-patches-line`] : [`${c}-${kind}`]);
  }

  async function setLayer(kind, on) {
    state.layers[kind] = on;
    if (on && (kind === "patches" || kind === "cos")) await ensureVectors(kind);
    layerIds(kind).forEach(id => map.getLayer(id) && map.setLayoutProperty(id, "visibility", vis(on)));
    renderWords();
  }

  function setOpacity(v) {
    state.opacity = v;
    CASE_ORDER.filter(c => state.results[c]).forEach(c => {
      RASTERS.forEach(k => map.setPaintProperty(`${c}-${k}`, "raster-opacity", v));
      map.setPaintProperty(`${c}-cos`, "line-opacity", v);
      map.setPaintProperty(`${c}-patches-line`, "line-opacity", v);
      map.setPaintProperty(`${c}-patches-fill`, "fill-opacity", 0.3 * v);
    });
  }

  // ---------- Camera ----------
  function moveAndWait(fn) {
    return new Promise(res => {
      let done = false;
      const finish = () => { if (!done) { done = true; res(); } };
      map.once("moveend", finish);
      fn();
      // jumpTo and zero-length moves can finish synchronously or not fire at all.
      setTimeout(finish, reduced() ? 50 : 12000);
    });
  }
  const areaCamera = caseId => {
    const b = state.results[caseId].aoi.bbox_wgs84;
    const cam = map.cameraForBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 60 });
    return { center: cam.center, zoom: Math.min(cam.zoom, 13.2), pitch: reduced() ? 0 : 38, bearing: reduced() ? 0 : -12 };
  };
  function go(cam, duration) {
    if (reduced() || !duration) return moveAndWait(() => map.jumpTo(cam));
    return moveAndWait(() => map.flyTo({ ...cam, duration, curve: 1.5, essential: false }));
  }
  async function flyIn() {
    const token = ++state.tour;
    if (!reduced()) {
      await go(GLOBE, 0);
      await go(PORTUGAL, 4200);
      if (token !== state.tour) return;
    }
    await go(areaCamera(state.caseId), 3800);
  }
  // A user drag, scroll or key press during the tour stops the remaining steps.
  map.on("movestart", e => { if (e.originalEvent) state.tour++; });

  // ---------- HUD (camera readout only) ----------
  let hudFrame = 0;
  function updateHud() {
    hudFrame = 0;
    const c = map.getCenter();
    $("hud-latlon").textContent = `${window.gevToDMS(c.lat, "lat")} ${window.gevToDMS(c.lng, "lon")}`;
    $("hud-zoom").textContent = map.getZoom().toFixed(1);
    $("hud-pitch").textContent = Math.round(map.getPitch()) + "°";
  }
  map.on("move", () => { if (!hudFrame) hudFrame = requestAnimationFrame(updateHud); });

  // ---------- Panel ----------
  function renderCaseButtons() {
    const box = $("cases");
    box.innerHTML = "";
    CASE_ORDER.filter(c => state.index.cases[c]).forEach(c => {
      const b = document.createElement("button");
      b.type = "button"; b.dataset.case = c; b.textContent = SHORT[c] || c;
      b.setAttribute("aria-pressed", String(c === state.caseId));
      b.addEventListener("click", () => selectCase(c, true));
      box.appendChild(b);
    });
  }

  function addMarkers() {
    CASE_ORDER.filter(c => state.index.cases[c]).forEach(c => {
      const meta = state.index.cases[c];
      const el = document.createElement("button");
      el.type = "button"; el.className = "site-marker"; el.textContent = SHORT[c] || c;
      el.setAttribute("aria-label", `Fly to ${SHORT[c] || c}`);
      el.setAttribute("aria-pressed", String(c === state.caseId));
      el.addEventListener("click", ev => { ev.stopPropagation(); selectCase(c, true); });
      // index.json stores center as [lat, lon].
      // The two areas are 40 km apart, so at globe scale the labels would overlap: stack them vertically.
      const dy = c === CASE_ORDER[0] ? -13 : 13;
      state.markers[c] = new maplibregl.Marker({ element: el, anchor: "left", offset: [10, dy] }).setLngLat([meta.center[1], meta.center[0]]).addTo(map);
    });
  }

  function row(label, value, status, sub, key) {
    return `<tr><td>${label} ${badge(status)}${sub ? `<span class="muted">${sub}</span>` : ""}</td><td class="n"${key ? ` data-key="${esc(key)}"` : ""}>${value}</td></tr>`;
  }

  function renderNumbers() {
    const r = state.results[state.caseId];
    if (!r) { $("numbers").innerHTML = `<p class="err" role="alert">results.json for this area could not be loaded. No numbers or change layers are shown.</p>`; return; }
    const c = r.change, cov = r.coverage, th = r.threshold, d0 = day(r.dates.before), d1 = day(r.dates.after);
    let rows = "";
    if (r.status !== "ok") rows += `<tr><td colspan="2" class="err">Run status: ${esc(r.status)}.</td></tr>`;
    rows += row("Images compared", `${d0} → ${d1}`, "public_observation", "Sentinel-2 L2A catalogue dates", "dates");
    rows += row("Index", esc(r.web.index_label), null, "method setting, not a result", "web.index_label");
    rows += row("Study box", `${fmt(r.aoi.area_km2, 1)} km²`, null, "method setting: a public bounding box, no parcel boundaries", "aoi.area_km2");
    rows += row("Pixels valid on both dates", `${fmt(cov.joint_valid_pixels_main)} (${pct(cov.joint_valid_fraction_main)})`, cov.data_status, null, "coverage.joint_valid_fraction_main");
    rows += row("Threshold |Δ|", fmt(th.value, 3), "observation_derived_result", esc(th.rule), "threshold.value");
    rows += row("Control pair flagged", pct(c.control_flagged_share_at_threshold, 2), c.data_status, "two images 20 days apart in the same summer: a false-alarm proxy", "change.control_flagged_share_at_threshold");
    rows += row(`Increase, patches ≥ ${fmt(c.min_patch_ha)} ha`, `${fmt(c.increase_area_ha, 0)} ha (${pct(c.increase_share_of_valid)})`, c.data_status, esc(r.web.legend.increase.label), "change.increase_area_ha");
    rows += row(`Decrease, patches ≥ ${fmt(c.min_patch_ha)} ha`, `${fmt(c.decrease_area_ha, 0)} ha (${pct(c.decrease_share_of_valid)})`, c.data_status, esc(r.web.legend.decrease.label), "change.decrease_area_ha");
    rows += row("Increase patches (median size)", `${fmt(c.increase_patches.patches_ge_min)} (${fmt(c.increase_patches.patch_area_ha_median, 1)} ha)`, c.data_status, null, "change.increase_patches.patches_ge_min");
    if (r.delta_centering && r.delta_centering.method !== "none") {
      rows += row("Scene-wide shift removed", fmt(r.delta_centering.raw_median_delta_main, 3), "observation_derived_result", "difference centred on the study-box median", "delta_centering.raw_median_delta_main");
    }
    if (r.seasonal_split) {
      const s = r.seasonal_split;
      rows += row("Increase pixels stable May → Aug", pct(s.stable_within_year / s.with_valid_second_date), s.data_status, "consistent with evergreen permanent crops; not confirmed", "seasonal_split");
    }
    $("numbers").innerHTML = `<table><caption class="sr-only">Key numbers for ${esc(r.title)}, read from results.json</caption>${rows}</table><p class="muted">Source: <a href="${DATA}${state.caseId}/results.json">results.json</a>, run <code>${esc(r.run_id)}</code>.</p>`;
  }

  function renderSure() {
    const rob = state.robustness[state.caseId];
    if (!rob) { $("sure").innerHTML = '<p class="muted">No robustness.json for this area, so no uncertainty is shown.</p>'; return; }
    const parts = [];
    parts.push(`<p>${badge(rob.data_status)}</p>`);
    parts.push(`<p><b>What is compared:</b> ${esc(rob.reference.flag)} against ${esc(rob.reference.reference_positive)}.</p>`);
    parts.push(`<p class="muted">Reads as: ${esc(rob.reference.reading)}.</p>`);
    const bkey = "pixel, 500 m blocks";
    const b = rob.bootstrap && rob.bootstrap.results && rob.bootstrap.results[bkey];
    if (b) {
      const ci = m => `${fmt(m.estimate * 100, 0)} % <span class="muted">(95 % range ${fmt(m.ci_low * 100, 0)}–${fmt(m.ci_high * 100, 0)} %)</span>`;
      parts.push(`<p data-key="bootstrap.precision"><span class="big">${ci(b.precision)}</span><br>of flagged pixels fall in the COS reference class (precision).</p>`);
      parts.push(`<p data-key="bootstrap.recall"><span class="big">${ci(b.recall)}</span><br>of COS reference pixels are flagged (recall).</p>`);
      parts.push(`<p class="muted">Spatial block bootstrap, ${fmt(b.block_m)} m blocks, ${fmt(b.iterations)} draws. ${esc(rob.bootstrap.caveat)}</p>`);
    }
    const o = rob.date_pairs && rob.date_pairs.increase_overlap_main_vs_second;
    const k = o && Object.keys(o).find(x => x.startsWith("both_at_main_threshold"));
    if (k) parts.push(`<p data-key="date_pairs.overlap"><b>Second date pair</b> (a few days from the first, same rule): <span class="big">${pct(o[k].share_of_a_also_in_b, 0)}</span> of flagged pixels are flagged again.</p>`);
    if (rob.checks) {
      const flat = [];
      const walk = v => { if (typeof v === "boolean") flat.push(v); else if (v && typeof v === "object") Object.values(v).forEach(walk); };
      walk(rob.checks);
      parts.push(`<p class="muted">Internal consistency checks in robustness.json: ${flat.filter(Boolean).length} of ${flat.length} passed.</p>`);
    }
    const ind = state.independent[state.caseId];
    if (ind) parts.push(`<p class="muted">Separate re-computation (independent_check.json): ${ind.all_match ? `all ${fmt(ind.comparisons.length)} headline numbers match` : "<b>mismatch found</b>"}.</p>`);
    parts.push(`<p class="muted">Source: <a href="${DATA}${state.caseId}/robustness.json">robustness.json</a>. Agreement with COS is not ground-truth accuracy.</p>`);
    $("sure").innerHTML = parts.join("");
  }

  function renderLayers() {
    const r = state.results[state.caseId];
    if (!r) { $("layers").innerHTML = ""; return; }
    const d0 = day(r.dates.before), d1 = day(r.dates.after);
    const defs = [
      ["after", `Sentinel-2 true colour, ${d1}`, "public_observation"],
      ["before", `Sentinel-2 true colour, ${d0}`, "public_observation"],
      ["delta", `${r.web.index_label} difference (${d1} − ${d0})`, "observation_derived_result"],
      ["change", `Candidate change (thresholded, ≥ ${fmt(r.change.min_patch_ha)} ha)`, "observation_derived_result"],
      ["patches", "Change patches (click a patch for details)", "observation_derived_result"],
      ["cos", "COS 2025 permanent crops and mines (reference)", "public_observation"],
    ];
    $("layers").innerHTML = "";
    defs.forEach(([k, label, st]) => {
      const lab = document.createElement("label");
      lab.className = "layer";
      lab.innerHTML = `<input type="checkbox" id="ly-${k}" ${state.layers[k] ? "checked" : ""}> <span>${esc(label)} ${badge(st)}</span>`;
      lab.querySelector("input").addEventListener("change", e => setLayer(k, e.target.checked));
      $("layers").appendChild(lab);
    });
    const lg = r.web.legend;
    $("legend").innerHTML = `<p><span class="sw" data-c="${esc(lg.increase.color)}"></span>${esc(lg.increase.label)}<br><span class="sw" data-c="${esc(lg.decrease.color)}"></span>${esc(lg.decrease.label)}</p>` +
      `<p class="muted">COS outlines: light green = permanent crops (2.2.x), yellow = mines and quarries (1.6.x). Dashed white box = study box. Basemap: Esri World Imagery, not part of the analysis.</p>`;
    $("legend").querySelectorAll(".sw").forEach(s => { s.style.background = s.dataset.c; });
  }

  function renderWords() {
    const r = state.results[state.caseId];
    if (!r) { $("map-words").textContent = "Results could not be loaded, so the map shows only the satellite basemap."; return; }
    const c = r.change, d0 = day(r.dates.before), d1 = day(r.dates.after);
    const on = Object.entries(state.layers).filter(([, v]) => v).map(([k]) => ({ after: `the ${d1} image`, before: `the ${d0} image`, delta: "the continuous difference", change: "candidate change", patches: "change patches", cos: "COS outlines" }[k]));
    $("map-words").textContent =
      `${r.title}. The globe is centred on a ${fmt(r.aoi.area_km2, 1)} km² study box in southern Portugal. ` +
      `${r.web.index_label} was compared between ${d0} and ${d1}. ` +
      `Candidate change in patches of at least ${fmt(c.min_patch_ha)} ha covers ${fmt(c.increase_area_ha, 0)} ha of increase (${pct(c.increase_share_of_valid)} of valid pixels) and ${fmt(c.decrease_area_ha, 0)} ha of decrease (${pct(c.decrease_share_of_valid)}). ` +
      `Layers now shown: ${on.length ? on.join(", ") : "none"}. The map shows where the surface changed, not why.`;
  }

  function renderHudTarget() {
    const r = state.results[state.caseId];
    $("hud-target").textContent = (SHORT[state.caseId] || state.caseId || "–").toUpperCase();
    $("hud-before").textContent = r ? r.dates.before.slice(0, 16).replace("T", " ") + " UTC" : "–";
    $("hud-after").textContent = r ? r.dates.after.slice(0, 16).replace("T", " ") + " UTC" : "–";
  }

  function renderFiles() {
    const base = DATA + state.caseId + "/";
    $("files").innerHTML = ["results.json", "robustness.json", "manifest.json", "patches.geojson", "reference_cos.json"].map(f => `<a href="${base}${f}">${f}</a>`).join(" · ");
  }

  async function selectCase(caseId, fly) {
    state.caseId = caseId;
    history.replaceState(null, "", "#" + caseId);
    document.querySelectorAll("#cases button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.case === caseId)));
    Object.entries(state.markers).forEach(([c, m]) => m.getElement().setAttribute("aria-pressed", String(c === caseId)));
    $("case-desc").textContent = state.index.cases[caseId].description || "";
    renderNumbers(); renderSure(); renderLayers(); renderWords(); renderHudTarget(); renderFiles();
    $("live").textContent = `Showing ${SHORT[caseId] || caseId}.`;
    if (fly && state.results[caseId]) {
      state.tour++;
      await go(areaCamera(caseId), 3000);
    }
  }

  // ---------- Start ----------
  (async () => {
    try { state.index = await getJSON(DATA + "index.json"); }
    catch (e) {
      $("numbers").innerHTML = `<p class="err" role="alert">The case-study index could not be loaded (${esc(e.message)}).</p>`;
      return;
    }
    const ids = CASE_ORDER.filter(c => state.index.cases[c]);
    await Promise.all(ids.map(async c => {
      const base = DATA + c + "/";
      const [res, rob, ind] = await Promise.all([
        getJSON(base + "results.json").catch(() => null),
        getJSON(base + "robustness.json", true).catch(() => null),
        getJSON(base + "independent_check.json", true).catch(() => null),
      ]);
      if (res) state.results[c] = res;
      if (rob) state.robustness[c] = rob;
      if (ind) state.independent[c] = ind;
    }));
    const fromHash = decodeURIComponent(location.hash.slice(1));
    state.caseId = ids.includes(fromHash) ? fromHash : ids[0];
    renderCaseButtons();
    await mapLoaded;
    map.addSource("aoi", { type: "geojson", data: { type: "FeatureCollection", features: ids.filter(c => state.results[c]).map(c => bboxPolygon(state.results[c].aoi.bbox_wgs84)) } });
    map.addLayer({ id: "aoi-line", type: "line", source: "aoi", paint: { "line-color": "#ffffff", "line-width": 1.6, "line-dasharray": [3, 2] } });
    ids.filter(c => state.results[c]).forEach(addCaseLayers);
    addMarkers();
    await selectCase(state.caseId, false);
    updateHud();

    $("opacity").addEventListener("input", e => { const v = Number(e.target.value); setOpacity(v); e.target.setAttribute("aria-valuetext", Math.round(100 * v) + " %"); });
    $("btn-globe").addEventListener("click", () => { state.tour++; go(GLOBE, 3000); });
    $("btn-portugal").addEventListener("click", () => { state.tour++; go(PORTUGAL, 3000); });
    $("btn-area").addEventListener("click", () => { state.tour++; go(areaCamera(state.caseId), 3000); });
    $("btn-tour").addEventListener("click", () => flyIn());
    window.addEventListener("hashchange", () => { const h = decodeURIComponent(location.hash.slice(1)); if (ids.includes(h) && h !== state.caseId) selectCase(h, true); });
    document.querySelector(".skip").addEventListener("click", e => { e.preventDefault(); $("panel").focus(); });
    document.body.dataset.ready = "1";
    flyIn();
  })();
})();
