const CACHE_NAME = 'eme-os-v1';
const urlsToCache = [
    '/',
    '/static/eme-logo.svg',
    'https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta20/dist/css/tabler.min.css',
    'https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css',
    'https://unpkg.com/vue@3/dist/vue.global.prod.js',
    'https://cdn.jsdelivr.net/npm/vue3-sfc-loader@0.8.4/dist/vue3-sfc-loader.js',
    'https://unpkg.com/jsqr/dist/jsQR.js'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    
    // Default strategy: Network First, fallback to cache
    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});
