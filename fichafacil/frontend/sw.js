/**
 * FichaFácil MVP - Service Worker
 * Enables PWA functionality, offline caching, and push notifications.
 */

const CACHE_NAME = 'fichafacil-v15';  // Refresh mobile clients after LAN auth/CORS fixes
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/empleado.html',
  '/dashboard.html',
  '/js/api.js',
  '/js/utils.js',
  '/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip API calls and SSE - always go to network
  if (url.pathname.startsWith('/api') || 
      url.pathname.startsWith('/auth') ||
      url.pathname.startsWith('/fichajes') ||
      url.pathname.startsWith('/negocios') ||
      url.pathname.startsWith('/correcciones') ||
      url.pathname.startsWith('/pdf') ||
      url.pathname.startsWith('/sse')) {
    return;
  }
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone and cache successful responses
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME)
            .then((cache) => cache.put(event.request, responseClone));
        }
        return response;
      })
      .catch(() => {
        // Fallback to cache
        return caches.match(event.request)
          .then((response) => {
            if (response) {
              return response;
            }
            // If no cache, return offline page for navigation
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
            return new Response('Offline', { status: 503 });
          });
      })
  );
});

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};
  const title = data.title || 'FichaFácil';
  const options = {
    body: data.body || 'Nueva notificación',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'general',
    requireInteraction: data.requireInteraction || false,
    data: {
      url: data.url || '/'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click - open relevant page
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const url = event.notification.data?.url || '/dashboard.html';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Check if there's already a window/tab open
        for (let client of windowClients) {
          if (client.url.includes('/dashboard') || client.url.includes('/empleado')) {
            return client.focus();
          }
        }
        // Open new window
        return clients.openWindow(url);
      })
  );
});

// Message handler for local notifications
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { title, body, tag } = event.data;
    self.registration.showNotification(title, {
      body: body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      vibrate: [200, 100, 200],
      tag: tag || 'local-notification'
    });
  }
  
  // Schedule daily reminder
  if (event.data && event.data.type === 'SCHEDULE_REMINDER') {
    scheduleExitReminder();
  }
});

// Schedule exit reminder at 18:00
function scheduleExitReminder() {
  const now = new Date();
  const reminderTime = new Date();
  reminderTime.setHours(18, 0, 0, 0);
  
  // If already past 18:00, schedule for tomorrow
  if (now >= reminderTime) {
    reminderTime.setDate(reminderTime.getDate() + 1);
  }
  
  const delay = reminderTime.getTime() - now.getTime();
  
  setTimeout(() => {
    self.registration.showNotification('⏰ Recordatorio FichaFácil', {
      body: '¿Has fichado la salida hoy? No olvides registrar tu jornada.',
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      vibrate: [300, 100, 300],
      tag: 'exit-reminder',
      requireInteraction: true,
      data: { url: '/empleado.html' }
    });
    // Reschedule for next day
    scheduleExitReminder();
  }, delay);
}
