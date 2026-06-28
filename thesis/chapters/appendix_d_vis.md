# Appendix D: Supplementary Visualizations

This appendix details the operational interface elements and chart rendering structures implemented on the interactive web dashboard.

## D.1 Anomaly Mapping Canvas
The geographic visualizer utilizes CartoDB Dark Matter tiles (`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`) as the basemap layer. This dark color scheme reduces visual clutter, maximizing the contrast of the highlighted fluorescent anomaly indicators. The spatial coordinates of anomalies are rendered using custom Leaflet `divIcon` marker objects. The markers include concentric pulsing rings styled using CSS keyframe animations:
```css
@keyframes markerPulse {
    0% { transform: scale(0.5); opacity: 1; }
    100% { transform: scale(2.5); opacity: 0; }
}
```

## D.2 Dual-Canvas Image Split Slider
To permit detailed visual comparison of before-and-after satellite tiles without loading heavy GIS software libraries, the dashboard implements a dual-canvas clipping slider. Two HTML5 `<canvas>` elements are loaded dynamically. The baseline historical tile is drawn to the lower canvas, and the anomalous tile is drawn to the upper canvas. An absolute-positioned vertical divider handle monitors horizontal pointer drag events (`mousemove` and `touchmove`) to compute the division percentage. The upper canvas is cropped using the hardware-accelerated CSS `clip-path` property:
```css
clip-path: inset(0 0 0 splitXpx);
```
This dynamic crop displays the baseline image on the left side of the divider and the anomaly image on the right side.

## D.3 Spectral Profile Radar Chart
The multi-spectral signature of each selected pixel is rendered on a radar chart using the Chart.js library within a transparent, glassmorphic card container. The chart displays four axes representing the computed NDVI, NDWI, BSI, and SWIR reflectance values. The signature of the selected pixel is rendered as a fluorescent cyan polygon, contrasted directly against a deep blue polygon representing the baseline mean. This visual design facilitates rapid verification of soil clearing or water flooding anomalies against expected local profiles.
