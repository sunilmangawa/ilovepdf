var CACHE_NAME = 'ilovepdf-shell-v2';
var APP_SHELL = [
    '/', '/offline/', '/static/css/modern.css', '/static/js/theme-switcher.js',
    '/static/js/pwa.js', '/static/img/favicon.ico',
    '/static/img/maskable/maskable_icon_x192.png', '/static/img/maskable/maskable_icon_x512.png'
];

// Cache on install


self.addEventListener("install", event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
    )
});

// Clear cache on activate
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => cacheName !== CACHE_NAME)
                    .map(cacheName => caches.delete(cacheName))
            );
        })
    );
});

// Serve from Cache
self.addEventListener("fetch", event => {
    if (event.request.method !== 'GET') return;
    var requestUrl = new URL(event.request.url);
    if (requestUrl.origin !== self.location.origin) return;
    if (event.request.mode === 'navigate') {
        event.respondWith(fetch(event.request).then(function (response) {
            var copy = response.clone();
            caches.open(CACHE_NAME).then(function (cache) { cache.put(event.request, copy); });
            return response;
        }).catch(function () { return caches.match(event.request).then(function (cached) {
            return cached || caches.match('/offline/');
        }); }));
        return;
    }
    event.respondWith(caches.match(event.request).then(function (cached) {
        return cached || fetch(event.request).then(function (response) {
            if (response.ok) {
                var copy = response.clone();
                caches.open(CACHE_NAME).then(function (cache) { cache.put(event.request, copy); });
            }
            return response;
        });
    }));
});
