# Version 6 globe view: sources, licences and reuse

Page: [`docs/index6.html`](../index6.html). Code: `docs/v6/app.js`, `docs/v6/v6.css`, `docs/v6/vendor/gev-dms.js`.
Research date: 27 November 2026. Licences were read from each project's `LICENSE` file through the GitHub API, not from the repository badge.

## What the owner asked for

"Implement God's Eye from GitHub as version 6." This page takes the look of the open-source God's Eye View globe (dark console, heads-up readouts, a camera that flies from the whole Earth down to a target) and points it at the thesis's real Portuguese Sentinel-2 case study. It is not a copy or a deployment of God's Eye View. It shows no live feeds, aircraft, ships, cameras or AI voice.

## Projects found

| Project | Licence (from `LICENSE`) | Stack | Last commit (UTC) | Use here |
|---|---|---|---|---|
| [bilawalsidhu/gods-eye-view](https://github.com/bilawalsidhu/gods-eye-view) (the original "God's Eye View") | MIT, Copyright (c) 2026 Bilawal Sidhu. The file adds that bundled and fetched **data** keep their own licences (for example TeleGeography CC BY-NC-SA, OSM ODbL) | Vue 3, Pinia, CesiumJS ^1.124, Vite; Google Photorealistic 3D Tiles; OpenAI Realtime for voice | `cee2940484ca`, 2026-11-27 06:52 | **One function copied** (see below). Visual inspiration for the HUD and reticle. No data copied |
| [koala73/worldmonitor](https://github.com/koala73/worldmonitor) | AGPL-3.0 | TypeScript, Preact, MapLibre GL ^6.4, deck.gl ^9.4, globe.gl, Vite | `e62f2fd94bd5`, 2026-11-27 10:49 | Inspiration only. **No code copied** (AGPL) |
| [BigBodyCobain/Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker) | AGPL-3.0 | Python back end; Next.js 16, React 19, MapLibre GL ^6.18 front end | `7d0803988426`, 2026-11-26 07:11 | Inspiration only. **No code copied** (AGPL) |
| [VrushankPatel/godseye](https://github.com/VrushankPatel/godseye) | Apache-2.0 | React 19, CesiumJS ^1.139, Vite | `eb4b8db218cb`, 2026-09-13 | Read only. Nothing copied |
| [alkeincodes/gods-eye](https://github.com/alkeincodes/gods-eye) | MIT, Copyright (c) 2026 Kane Dev | React 19, CesiumJS ^1.139, Tailwind, Vite | `e7c2d6ea39a4`, 2026-04-14 | Read only. Nothing copied |
| [noaRoblesLevy/GodsEye](https://github.com/noaRoblesLevy/GodsEye) | No licence file (all rights reserved by default) | CesiumJS ^1.139, Vite | `a047ff3e2b7b`, 2026-03-05 | **Not usable.** Nothing copied |
| [adityabandi/Gods_Eye](https://github.com/adityabandi/Gods_Eye) | GPL-3.0 | not stated | `3399074a3733`, 2026-05-08 | **No code copied** (GPL) |
| [uhrichsam4/gods-eye-view](https://github.com/uhrichsam4/gods-eye-view), [electronictechshow-netizen/gods-eye-view-free](https://github.com/electronictechshow-netizen/gods-eye-view-free) | MIT (Bilawal Sidhu's notice, unchanged) | Forks of the original | 2026-09-01, 2026-10-06 | Forks; the original was used instead |

Search method: `gh search repos` for "gods eye", "gods eye view", "worldmonitor", "osint globe", "spatial intelligence globe" and "shadowbroker", sorted by stars, plus one web search. Other repositories named "GodsEye" (an exam proctoring system, a face-login hack, a C++ OS project, a Chinese location app) are unrelated to globe dashboards and were skipped.

## Why MapLibre and not CesiumJS

Most God's Eye clones use CesiumJS. CesiumJS works without a key only with its own low-resolution imagery; the original project's look depends on Google Photorealistic 3D Tiles, which need an API key. This repository publishes no keys. MapLibre GL JS has a globe projection with an atmosphere, takes any raster tile source and places the thesis's georeferenced PNG/JPG overlays directly. It is also what worldmonitor and Shadowbroker use.

I pinned **MapLibre GL JS 5.24.1**, not the newest 6.19.0. Version 6 ships only as ES modules and loads a separate worker file at run time, so a single Subresource Integrity hash cannot cover all the code it runs. Version 5.24.1 is one UMD file with the worker inside it, so the SRI hash below covers everything.

## Libraries and external services

| Item | Version | Licence | How it is loaded |
|---|---|---|---|
| MapLibre GL JS | 5.24.1 (published 2026-11-11) | BSD-3-Clause | jsDelivr, pinned, SRI below |
| Esri World Imagery tiles | live service | Esri terms of use; attribution shown on the map | `server.arcgisonline.com`, no key. The same basemap as `docs/case-study/index.html` |
| God's Eye View `_toDMS` | upstream commit `cee2940484ca` | MIT | copied into `docs/v6/vendor/gev-dms.js` |

Subresource Integrity hashes (SHA-384 of the files served by jsDelivr on 27 November 2026):

| File | Bytes | Integrity |
|---|---|---|
| `https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.1/dist/maplibre-gl.js` | 1,058,059 | `sha384-nXMl9YiLoSG5KBPTFgvxVuIqQQcqIvo0bFrvoEaGJC6r7IibIzF1S36Zbf/sKBtL` |
| `https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.1/dist/maplibre-gl.css` | 70,024 | `sha384-uTttxo/aOKbdE5RlD/SPzSDoDmNvGlUYPjONi2MN/b7c9HPSvW07OIuyP7uL6jxK` |

To recompute: `curl -sL <url> | openssl dgst -sha384 -binary | openssl base64 -A`.

## What was copied, exactly

One function: `_toDMS(decimal, type)` from `src/hud.js` of God's Eye View (blob `97a898bac26338f16b94917b264969123a9a2a13`). It turns a decimal latitude or longitude into degrees, minutes and seconds, for example `37°57'07.25"N`. The class method became a standalone function `window.gevToDMS`; the arithmetic is unchanged. The MIT notice is kept at the top of `docs/v6/vendor/gev-dms.js` and repeated below. The page uses it only for the camera readout in the lower-left corner, which is labelled "camera readout, not data".

Nothing else was copied. The stylesheet, layout and `app.js` were written for this page. The 2D case-study page (`docs/case-study/index.html`) supplied the data-loading logic, the COS filter (2.2.x permanent crops, 1.6.x mines) and the patch popup text, which are reused here.

## Data on the page

Every number and layer comes from files already in `docs/case-study/data/<case>/`. Nothing is hard-coded and nothing is synthetic.

| Layer or panel | File | Data status |
|---|---|---|
| Sentinel-2 true colour, before and after | `overlay_before.jpg`, `overlay_after.jpg`, bounds from `results.json` `web.overlay_bounds_latlng` | public observation |
| Index difference, candidate change | `overlay_delta.png`, `overlay_change.png` | observation-derived result |
| Change patches | `patches.geojson` | observation-derived result (seasonal amplitude in popups: unverified interpretation) |
| COS 2025 outlines | `reference_cos2025v1.geojson` | public observation (DGT, CC-BY) |
| Key numbers | `results.json` | label read from each block's `data_status` |
| "How sure are we?" | `robustness.json` (bootstrap with 500 m blocks, second date pair, checks), `independent_check.json` | observation-derived result |
| Study boxes and markers | `results.json` `aoi.bbox_wgs84`, `index.json` `center` | method setting |

The globe, the fly-in, the reticle and the readouts are display only. They carry no data.

## Known issues found while building

- `case-study/data/alqueva_olive/robustness.json` stores `reference.source` and `reference.license` with double-encoded UTF-8 (`OcupaÃ§Ã£o` instead of `Ocupação`). The page does not show those two fields. The fix belongs in the pipeline that writes the file, which this change does not touch.
- `docs/_headers` sets a Content-Security-Policy without `worker-src blob:`. GitHub Pages ignores `_headers`, so the page works there. On a host that applies `_headers` (Netlify, Cloudflare Pages), MapLibre's worker would be blocked until `worker-src 'self' blob:` is added.

## Third-party notices

### God's Eye View (`docs/v6/vendor/gev-dms.js`)

```
MIT License

Copyright (c) 2026 Bilawal Sidhu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### MapLibre GL JS 5.24.1 (loaded from jsDelivr, not stored in this repository)

```
Copyright (c) 2023, MapLibre contributors

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of MapLibre GL JS nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

MapLibre's licence file also carries the BSD-3-Clause notice for mapbox-gl-js v1.13 and earlier (Copyright (c) 2020, Mapbox); see `https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.1/LICENSE.txt`.

## Browser check

Run on 27 November 2026 with Playwright for Python driving installed Google Chrome (headless, software WebGL). A local Python `http.server` served `docs/` under the `/tesis/` base path, the same path GitHub Pages uses.

| Check | Desktop 1440 × 900 | Mobile 390 × 844, reduced motion |
|---|---|---|
| Console errors and page errors | 0 | 0 |
| HTTP errors (status ≥ 400) | 0 | 0 |
| Numbers on the page vs `results.json` and `robustness.json` (both areas, 12 values each) | 24 of 24 match | 24 of 24 match |
| First Tab stop | skip link; Enter moves focus to the panel | same |
| Visible focus on the 14 Tab stops after the skip link | 3 px yellow outline on all | same |
| Camera 0.6 s after load | zoom 2.1, still flying | zoom 10.7, already at the study area (no flight) |

Not errors, but logged: Chrome's software renderer prints GPU performance warnings ("GPU stall due to ReadPixels"). MapLibre cancels basemap tile requests it no longer needs while the camera moves; these show as `ERR_ABORTED` and are expected. Colour contrast of every text and background pair in `v6.css` was computed with the WCAG formula; the lowest is 6.3:1 (amber badge in a white popup).

Screenshots: `screenshots/desktop-1440x900.png` and `screenshots/mobile-390x844-reduced-motion.png`.

Not tested: screen readers, Firefox and Safari, a real phone, and a GPU-accelerated browser.
