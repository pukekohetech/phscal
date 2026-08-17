const CACHE = 'phs-calendar-pwa-v14-install-fix';
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
    await cache.addAll(APP_SHELL);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)));
    if (self.registration.navigationPreload) {
      try { await self.registration.navigationPreload.enable(); } catch (_) { }
    }
    await self.clients.claim();
  })());
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

  // Navigations use network first so a deployed update is visible promptly,
  // while the cached app shell remains available offline.
  if (request.mode === 'navigate' && url.origin === self.location.origin) {
    event.respondWith((async () => {
      try {
        const preload = await event.preloadResponse;
        const response = preload || await fetch(request);
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put('./index.html', copy)).catch(() => {});
        }
        return response;
      } catch (_) {
        return (await caches.match(request)) || (await caches.match('./index.html'));
      }
    })());
    return;
  }

  // Same-origin static assets: cache first with a background refresh.
  if (url.origin === self.location.origin) {
    event.respondWith((async () => {
      const cached = await caches.match(request);
      const networkPromise = fetch(request).then(response => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(request, copy)).catch(() => {});
        }
        return response;
      });
      if (cached) {
        event.waitUntil(networkPromise.catch(() => {}));
        return cached;
      }
      try {
        return await networkPromise;
      } catch (_) {
        return caches.match('./index.html');
      }
    })());
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
