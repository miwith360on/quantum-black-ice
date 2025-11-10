// Service Worker for PWA - Offline Support & Caching
const CACHE_NAME = 'black-ice-v1.0.0';
const API_CACHE_NAME = 'black-ice-api-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
    '/mobile.html',
    '/mobile-styles.css',
    '/mobile.js',
    '/manifest.json',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://cdn.socket.io/4.5.4/socket.io.min.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS).catch(err => {
                console.error('[SW] Failed to cache some assets:', err);
            });
        }).then(() => {
            return self.skipWaiting(); // Activate immediately
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim(); // Take control immediately
        })
    );
});

// Fetch event - network first, fall back to cache
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Handle API requests with network-first strategy
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            networkFirstStrategy(event.request, API_CACHE_NAME, 5000) // 5 second timeout
        );
        return;
    }
    
    // Handle static assets with cache-first strategy
    if (STATIC_ASSETS.some(asset => event.request.url.includes(asset))) {
        event.respondWith(
            cacheFirstStrategy(event.request, CACHE_NAME)
        );
        return;
    }
    
    // Handle map tiles and external resources
    if (url.hostname.includes('openstreetmap.org') || 
        url.hostname.includes('rainviewer.com') ||
        url.hostname.includes('tile.openweathermap.org')) {
        event.respondWith(
            cacheFirstStrategy(event.request, CACHE_NAME, 86400000) // Cache for 1 day
        );
        return;
    }
    
    // Default: network first
    event.respondWith(
        networkFirstStrategy(event.request, CACHE_NAME)
    );
});

// Network-first strategy with timeout
async function networkFirstStrategy(request, cacheName, timeout = 10000) {
    try {
        // Race between network request and timeout
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Network timeout')), timeout)
        );
        
        const networkPromise = fetch(request).then(response => {
            // Only cache GET requests (POST/PUT/DELETE cannot be cached)
            if (response.ok && request.method === 'GET') {
                const responseClone = response.clone();
                caches.open(cacheName).then(cache => {
                    cache.put(request, responseClone);
                });
            }
            return response;
        });
        
        return await Promise.race([networkPromise, timeoutPromise]);
    } catch (error) {
        console.log('[SW] Network request failed, trying cache:', error.message);
        // Fall back to cache (only works for GET requests)
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page or error response
        return new Response(
            JSON.stringify({ 
                error: 'Offline', 
                message: 'No network connection and no cached data available' 
            }),
            { 
                status: 503, 
                headers: { 'Content-Type': 'application/json' } 
            }
        );
    }
}

// Cache-first strategy
async function cacheFirstStrategy(request, cacheName, maxAge = null) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        // Check if cache is too old
        if (maxAge) {
            const cachedDate = new Date(cachedResponse.headers.get('date'));
            const now = new Date();
            if (now - cachedDate > maxAge) {
                console.log('[SW] Cache expired, fetching fresh data');
                return fetchAndCache(request, cacheName);
            }
        }
        
        // Fetch update in background
        fetchAndCache(request, cacheName);
        return cachedResponse;
    }
    
    return fetchAndCache(request, cacheName);
}

// Fetch and cache helper
async function fetchAndCache(request, cacheName) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[SW] Fetch failed:', error);
        throw error;
    }
}

// Background sync for offline predictions
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);
    if (event.tag === 'sync-predictions') {
        event.waitUntil(syncPredictions());
    }
});

async function syncPredictions() {
    try {
        // Get any pending predictions from IndexedDB
        // Send them to the server when back online
        console.log('[SW] Syncing predictions...');
        // Implementation would go here
    } catch (error) {
        console.error('[SW] Sync failed:', error);
    }
}

// Push notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');
    
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Black Ice Alert';
    const options = {
        body: data.body || 'New weather alert in your area',
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-96.png',
        vibrate: [200, 100, 200],
        data: data,
        actions: [
            { action: 'view', title: 'View Details' },
            { action: 'dismiss', title: 'Dismiss' }
        ],
        requireInteraction: true
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event.action);
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/mobile.html?alert=' + (event.notification.data?.id || ''))
        );
    }
});

// Message handler for communication with app
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => caches.delete(cacheName))
                );
            }).then(() => {
                event.ports[0].postMessage({ success: true });
            })
        );
    }
});

console.log('[SW] Service worker loaded');
