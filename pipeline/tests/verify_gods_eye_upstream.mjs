/**
 * Optional official-upstream interoperability check.
 * Usage:
 *   node pipeline/tests/verify_gods_eye_upstream.mjs PATH_TO_GODS_EYE_CLONE
 * No packages installed, no remote traffic, no sensitive data transferred.
 */
import { readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const upstream = process.argv[2];
if (!upstream) throw new Error('Supply a local checkout of bilawalsidhu/gods-eye-view');
const bundlePath = resolve('docs/experimental/geo-intelligence/gods-eye/sentinel2-observed-2024-2025.gevbundle.json');
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
assert.equal(decoded.length, 116);
assert.ok(decoded.every((f) => f.type === 'Polygon'));
assert.ok(decoded.every((f) => f.coordinates[0][0][2] === 6500));
console.log('OFFICIAL GEV PARSER PASS; scene=1, data-pack=1, observed cells=116');
console.log('Scope: document/byte/geometry contract; NOT browser rendering, data accuracy, or validated event detection');
