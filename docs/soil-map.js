/* Context map only: never present this basemap as measured Sentinel-2 imagery. */
(async function () {
    const status = document.getElementById('soil-map-status');
    try {
        const response = await fetch('data/observed_alentejo_soil5_pair_20261123.json');
        if (!response.ok) throw new Error('Observation record HTTP ' + response.status);
        const record = await response.json();
        const b = record.bbox;
        if (!Array.isArray(b) || b.length !== 4 || !b.every(Number.isFinite) || b[0] >= b[2] || b[1] >= b[3] || b[0] < -180 || b[2] > 180 || b[1] < -90 || b[3] > 90) throw new Error('Invalid observation footprint');
        const bounds = [[b[1], b[0]], [b[3], b[2]]];
        const map = L.map('soil-map', { maxZoom: 18 });
        const imagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { attribution: 'Tiles &copy; Esri and imagery contributors', maxZoom: 18 });
        const streets = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>', maxZoom: 18 });
        imagery.addTo(map);
        document.getElementById('soil-basemap').addEventListener('change', event => {
            const street = event.target.value === 'street';
            map.removeLayer(street ? imagery : streets);
            (street ? streets : imagery).addTo(map).bringToBack();
        });
        L.rectangle(bounds, { color: '#fbbf24', weight: 3, fillOpacity: 0.12 }).addTo(map).bindPopup('Public paired-scene sampling footprint; not verified physical soil change.');
        map.fitBounds(bounds, { padding: [45, 45], maxZoom: 15 });
        const coords = b.map(n => n.toFixed(4)).join(', ');
        status.textContent = 'Observed study bounds (west, south, east, north): ' + coords;
        const properties = {
            phh2o: ['pH in water', 'Stored value / 10 = pH'],
            soc: ['Soil organic carbon', 'Stored value / 10 = g/kg'],
            nitrogen: ['Total nitrogen', 'Stored value / 100 = g/kg'],
            clay: ['Clay fraction', 'Stored value / 10 = % by mass'],
            sand: ['Sand fraction', 'Stored value / 10 = % by mass'],
            silt: ['Silt fraction', 'Stored value / 10 = % by mass'],
            bdod: ['Bulk density', 'Stored value / 100 = kg/dm^3'],
            cfvo: ['Coarse fragments', 'Stored value / 10 = volume %'],
            cec: ['Cation exchange capacity', 'Stored value / 10 = cmol(c)/kg']
        };
        const landCover = {
            'cos2018v4-s2': 'Portugal land use 2018 (COS Serie 2, v4)',
            'cos2025v1-s2': 'Portugal land use 2025 (COS Serie 2, v1)'
        };
        const select = document.getElementById('soil-layer');
        const opacity = document.getElementById('soil-opacity');
        const legend = document.getElementById('soil-legend');
        const legendImage = document.getElementById('soil-legend-image');
        const meta = document.getElementById('soil-layer-meta');
        const source = document.getElementById('soil-layer-source');
        let overlay = null;
        for (const [key, info] of Object.entries(properties)) {
            select.add(new Option(info[0], key));
        }
        for (const [key, name] of Object.entries(landCover)) {
            select.add(new Option(name, key));
        }
        select.addEventListener('change', () => {
            if (overlay) map.removeLayer(overlay);
            overlay = null;
            legend.hidden = true;
            const key = select.value;
            const isCOS = Object.hasOwn(landCover, key);
            if (!Object.hasOwn(properties, key) && !isCOS) {
                status.textContent = 'Observed study bounds (west, south, east, north): ' + coords;
                return;
            }
            const endpoint = isCOS ? 'https://geo2.dgterritorio.gov.pt/geoserver/COS-S2/wms' : 'https://maps.isric.org/mapserv?map=/map/' + key + '.map';
            const separator = endpoint.includes('?') ? '&' : '?';
            const layer = isCOS ? key : key + '_0-5cm_mean';
            const active = L.tileLayer.wms(endpoint, { layers: layer, format: 'image/png', transparent: true, version: '1.1.1', opacity: Number(opacity.value) / 100, attribution: isCOS ? 'Direcao-Geral do Territorio (DGT) - COS Serie 2' : 'ISRIC SoilGrids (CC BY 4.0)', maxZoom: 18 });
            overlay = active;
            let errors = 0;
            status.textContent = 'Loading reference overlay...';
            active.on('tileerror', () => { if (overlay === active) { errors++; status.textContent = 'Some reference tiles failed; this layer may be incomplete.'; } });
            active.on('load', () => { if (overlay === active && errors === 0) status.textContent = isCOS ? 'DGT land-use map loaded; reference classification, not a measured change event.' : 'SoilGrids modeled layer loaded; no independent laboratory validation.'; });
            active.addTo(map);
            legend.hidden = false;
            meta.textContent = isCOS ? landCover[key] + ' | Official photo-interpreted land-use reference; not independent field truth. See provider legend.' : properties[key][0] + ' | 0-5 cm | mean prediction | 250 m native grid. ' + properties[key][1] + '. See provider legend.';
            source.href = endpoint + separator + 'SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities';
            legendImage.src = endpoint + separator + 'SERVICE=WMS&VERSION=1.1.1&REQUEST=GetLegendGraphic&FORMAT=image/png&LAYER=' + layer;
        });
        opacity.addEventListener('input', () => { if (overlay) overlay.setOpacity(Number(opacity.value) / 100); });
        for (const layer of [imagery, streets]) layer.on('tileerror', () => { status.textContent = 'Some contextual tiles failed to load. Study bounds: ' + coords; });
    } catch (error) {
        status.textContent = 'Study map unavailable: ' + error.message + '. See the source observation record.';
    }
})();
