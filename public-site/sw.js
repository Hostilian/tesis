/* One-time retirement of the legacy cached dashboard.
 * This worker intentionally has no fetch handler: pages load from the network.
 */
self.addEventListener("install", event => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    await caches.delete("orbital-intel-v2");
    const openPages = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    await self.registration.unregister();

    // Refresh only this repository's GitHub Pages clients after removing its old cache.
    await Promise.all(openPages.map(async client => {
      const page = new URL(client.url);
      if (page.origin === self.location.origin && page.pathname.startsWith("/tesis/")) {
        await client.navigate(client.url);
      }
    }));
  })());
});
