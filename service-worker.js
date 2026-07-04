const CACHE = 'phs-calendar-pwa-v9-reliability';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.allSettled(APP_SHELL.map(url => cache.add(url)));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

function normalizedCalendarRequest(request){
  const url = new URL(request.url);
  url.searchParams.delete('_ts');
  return new Request(url.toString(), { method:'GET' });
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // App shell: cache first, then network, then fall back to index.html.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(response => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(request, copy)).catch(() => {});
        }
        return response;
      }).catch(() => caches.match('./index.html')))
    );
    return;
  }

  // Cross-origin calendar and weather requests: network first, cache last good copy.
  // Calendar feeds add _ts cache-busting params, so cache using a normalized URL.
  const cacheKey = normalizedCalendarRequest(request);
  event.respondWith(
    fetch(request).then(response => {
      if (response && response.ok) {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(cacheKey, copy)).catch(() => {});
      }
      return response;
    }).catch(() => caches.match(cacheKey))
  );
});
