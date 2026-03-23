const CACHE = 'phs-calendar-pwa-v2';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // App shell on same origin: network first for HTML, cache first for static assets.
  if (url.origin === self.location.origin) {
    const wantsHtml = request.mode === 'navigate' || request.destination === 'document' || url.pathname.endsWith('/index.html') || url.pathname === '/' || url.pathname === '';

    if (wantsHtml) {
      event.respondWith(
        fetch(request).then(response => {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put('./index.html', copy)).catch(() => {});
          return response;
        }).catch(() => caches.match(request).then(match => match || caches.match('./index.html')))
      );
      return;
    }

    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(response => {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(request, copy)).catch(() => {});
        return response;
      }))
    );
    return;
  }

  // Do not service-worker-cache remote calendar feeds.
  event.respondWith(fetch(request));
});
