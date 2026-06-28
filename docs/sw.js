// ============================================================
// ORBITAL INTELLIGENCE — Service Worker v2
// Provides offline capability (PWA) per master prompt §13.6
// Cache-first strategy for static assets;
// Network-first for dynamic API/data endpoints.
// ============================================================

const CACHE_VERSION = 'orbital-intel-v2';
const OFFLINE_URL = 'offline.html';

const STATIC_ASSETS = [
  './',
  'index.html',
  'index.css',
  'app.js',
  'manifest.json',
  'og_image.png',
  'apple-touch-icon.png',
  'icon-192.png',
  'icon-512.png',
  'favicon.ico',
  'offline.html',
  'locales/en.json',
  'locales/cs.json',
  'openapi.yaml',
  'api.html',
];

const DYNAMIC_DATA = [
  'data/anomalies.json',
  'data/regions.geojson',
  'api/v1/anomalies/index.json',
  'api/v1/datasets/index.json',
  'api/v1/status/index.json',
];

// ── Install: pre-cache static shell ───────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => {
      console.log('[SW] Pre-caching static assets');
      // Cache data separately (non-blocking) so missing tiles don't abort install
      cache.addAll(DYNAMIC_DATA).catch(err =>
        console.warn('[SW] Some dynamic assets not cached on install:', err)
      );
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// ── Activate: purge old caches ─────────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_VERSION)
          .map(key => {
            console.log('[SW] Removing old cache:', key);
            return caches.delete(key);
          })
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: cache-first for static, network-first for data ─────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignore non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) return;

  // Network-first for data files (always try to get fresh data)
  if (url.pathname.includes('/data/') || url.pathname.includes('/api/v1/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Cache-first for everything else (static shell)
  event.respondWith(cacheFirst(request));
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // For navigation requests, return offline fallback
    if (request.mode === 'navigate' || request.destination === 'document') {
      const offlinePage = await caches.match(OFFLINE_URL);
      if (offlinePage) return offlinePage;
    }
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ error: 'offline', cached: false }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
