/**
 * Optional official-upstream interoperability check.
 * Usage:
 *   node pipeline/tests/verify_gods_eye_upstream.mjs PATH_TO_GODS_EYE_CLONE [chile|portugal]
 * No packages installed, no remote traffic, no sensitive data transferred.
 */
import { readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const upstream = process.argv[2];
if (!upstream) throw new Error('Supply a local checkout of bilawalsidhu/gods-eye-view');
const variants = {
  chile: {path: 'docs/experimental/geo-intelligence/gods-eye/sentinel2-observed-2024-2025.gevbundle.json', cells: 116},
  portugal: {path: 'docs/experimental/geo-intelligence/gods-eye/sentinel2-portugal-alentejo-2025-2026.gevbundle.json', cells: 144},
};
const region = process.argv[3] ?? 'chile';
if (!Object.hasOwn(variants, region)) throw new Error('Unknown reviewed public region');
const bundlePath = resolve(variants[region].path);
const moduleUrl = (relative) => pathToFileURL(join(resolve(upstream), relative)).href;

const { parseSceneShare } = await import(moduleUrl('src/director/sharing/bundle.js'));
const { decodePackGeoJSON } = await import(moduleUrl('src/director/packs/geojson.js'));
const text = readFileSync(bundlePath, 'utf8');
const { project, assets } = await parseSceneShare(text);
assert.equal(project.scenes.length, 1);
const pack = project.scenes[0].dataPacks[0];
const asset = assets.get(pack.source.path);
assert.ok(asset, 'GEV official share parser must resolve the bundled asset');
const decoded = decodePackGeoJSON(asset.bytes);
assert.equal(decoded.length, variants[region].cells);
assert.ok(decoded.every((f) => f.type === 'Polygon'));
assert.ok(decoded.every((f) => f.coordinates[0][0][2] === 6500));
console.log(`OFFICIAL GEV PARSER PASS; region=${region}, scene=1, data-pack=1, observed cells=${decoded.length}`);
console.log('Scope: document/byte/geometry contract; NOT browser rendering, data accuracy, or validated event detection');
