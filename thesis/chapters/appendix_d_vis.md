# Appendix D: Supplementary Visualizations

This appendix details the operational interface elements and chart rendering structures implemented on the interactive web dashboard.

## D.1 Anomaly Mapping Canvas
*   **Basemap Tile Layer**: CartoDB Dark Matter tiles (`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`) are chosen to reduce visual noise and highlight fluorescent marker indicators.
*   **Pulsing Markers**: Custom Leaflet HTML `divIcon` elements are styled using CSS keyframe expansions. The pulsing ring expands dynamically:
    ```css
    @keyframes markerPulse {
        0% { transform: scale(0.5); opacity: 1; }
        100% { transform: scale(2.5); opacity: 0; }
    }
    ```

## D.2 Dual-Canvas Image Split Slider
*   To render comparison tiles without loading heavy packages, two HTML5 `<canvas>` elements are loaded.
*   The baseline image is painted to the lower canvas, and the anomaly image is painted to the upper canvas.
*   An absolute-positioned divider handle listens to horizontal pointer drag events (`mousemove` / `touchmove`) to calculate split percentages.
*   The anomaly canvas is dynamically cropped using the CSS `clip-path: inset(0 0 0 splitXpx)` rule, revealing the baseline on the left half and the anomaly on the right half.

## D.3 Spectral Profile Radar Chart
*   Rendered using Chart.js inside a responsive glass-container.
*   Maps four axis points representing NDVI, NDWI, BSI, and SWIR reflectance.
*   The selected pixel's signature is drawn in fluorescent cyan, contrasted with the baseline mean drawn in deep blue, allowing immediate visual verification of land-clearing vs. water-flooding anomalies.
