const CACHE_NAME = 'orbital-intel-v1';
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'index.css',
  'app.js',
  'manifest.json',
  'og_image.png',
  'apple-touch-icon.png',
  'favicon.ico',
  'data/anomalies.json',
  'data/regions.geojson',
  'locales/en.json',
  'locales/cs.json',
  'openapi.yaml',
  'api.html'
];

// Install Event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[Service Worker] Pre-caching static assets');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Event
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Interception
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        // Fallback for missing fetch offline
        console.log('[Service Worker] Fetch failed offline');
      });
    })
  );
});
