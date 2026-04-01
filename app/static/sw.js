// Service Worker for Truck Stops Directory PWA
var CACHE_NAME = 'stops-v1';
var PRECACHE_URLS = [
    '/',
    '/us',
    '/canada',
    '/brands',
    '/highways',
    '/rest-areas',
    '/weigh-stations',
];

// Install — precache core pages
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(PRECACHE_URLS);
        }).then(function() {
            return self.skipWaiting();
        })
    );
});

// Activate — clean old caches
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.filter(function(name) {
                    return name !== CACHE_NAME;
                }).map(function(name) {
                    return caches.delete(name);
                })
            );
        }).then(function() {
            return self.clients.claim();
        })
    );
});

// Fetch — network first, fallback to cache
self.addEventListener('fetch', function(event) {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip API requests, auth pages, and external resources
    var url = new URL(event.request.url);
    if (url.origin !== self.location.origin) return;
    if (url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/login') ||
        url.pathname.startsWith('/verify') ||
        url.pathname.startsWith('/logout')) {
        return;
    }

    event.respondWith(
        fetch(event.request).then(function(response) {
            // Cache successful HTML and static asset responses
            if (response.status === 200) {
                var responseClone = response.clone();
                caches.open(CACHE_NAME).then(function(cache) {
                    cache.put(event.request, responseClone);
                });
            }
            return response;
        }).catch(function() {
            // Network failed — try cache
            return caches.match(event.request).then(function(cached) {
                return cached || new Response(
                    '<!doctype html><html><head><title>Offline</title>' +
                    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
                    '<style>body{font-family:sans-serif;text-align:center;padding:60px 20px;' +
                    'background:#f8fafc;color:#0f172a}h1{color:#0f2440}p{color:#64748b}</style>' +
                    '</head><body><h1>You are offline</h1>' +
                    '<p>Please check your internet connection and try again.</p>' +
                    '<button onclick="location.reload()">Retry</button></body></html>',
                    {status: 503, headers: {'Content-Type': 'text/html'}}
                );
            });
        })
    );
});
