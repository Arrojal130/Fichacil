/**
 * FichaFácil MVP - Utilities
 * Common helper functions.
 */

// Encapsulado en IIFE para evitar polución del scope global
(function() {
'use strict';

/**
 * Get current geolocation.
 * Returns { lat, lon } or null if denied/unavailable.
 */
async function getGeolocation(timeout = 10000) {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            console.log('⚠️ Geolocation not supported');
            resolve(null);
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            (error) => {
                console.log('⚠️ Geolocation error:', error.message);
                resolve(null);
            },
            {
                enableHighAccuracy: true,
                timeout: timeout,
                maximumAge: 60000 // 1 minute cache
            }
        );
    });
}

/**
 * Format date for display.
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Format time for display.
 */
function formatTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Format datetime for display.
 */
function formatDateTime(dateStr) {
    return `${formatDate(dateStr)} ${formatTime(dateStr)}`;
}

/**
 * Format distance in meters/km.
 */
function formatDistance(meters) {
    if (meters === null || meters === undefined) {
        return 'Sin ubicación';
    }
    if (meters < 1000) {
        return `${Math.round(meters)}m`;
    }
    return `${(meters / 1000).toFixed(1)}km`;
}

/**
 * Show toast notification.
 */
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast fixed top-4 left-1/2 transform -translate-x-1/2 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Vibrate on mobile
    if (navigator.vibrate) {
        navigator.vibrate(type === 'success' ? [100] : [50, 50, 50]);
    }
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show loading spinner.
 */
function showLoading(container) {
    const loader = document.createElement('div');
    loader.className = 'loading-spinner flex items-center justify-center p-8';
    loader.innerHTML = `
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
    `;
    container.appendChild(loader);
    return loader;
}

/**
 * Hide loading spinner.
 */
function hideLoading(loader) {
    if (loader) loader.remove();
}

/**
 * Play sound feedback.
 */
function playSound(type = 'success') {
    // Using Web Audio API for cross-browser support
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    if (type === 'success') {
        oscillator.frequency.value = 800;
        gainNode.gain.value = 0.1;
        oscillator.start();
        setTimeout(() => {
            oscillator.frequency.value = 1000;
        }, 100);
        setTimeout(() => {
            oscillator.stop();
        }, 200);
    } else {
        oscillator.frequency.value = 300;
        gainNode.gain.value = 0.1;
        oscillator.start();
        setTimeout(() => {
            oscillator.stop();
        }, 300);
    }
}

/**
 * Get today's date in YYYY-MM-DD format.
 */
function getTodayISO() {
    return new Date().toISOString().split('T')[0];
}

/**
 * Get date N days ago in YYYY-MM-DD format.
 */
function getDateDaysAgo(days) {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date.toISOString().split('T')[0];
}

/**
 * Debounce function for search inputs.
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Store last fichaje for offline display.
 */
function storeLastFichaje(data) {
    localStorage.setItem('lastFichaje', JSON.stringify({
        ...data,
        storedAt: new Date().toISOString()
    }));
}

/**
 * Get stored last fichaje.
 */
function getStoredLastFichaje() {
    const stored = localStorage.getItem('lastFichaje');
    return stored ? JSON.parse(stored) : null;
}

/**
 * Store session data.
 */
function storeSession(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value));
}

/**
 * Get session data.
 */
function getSession(key) {
    const stored = sessionStorage.getItem(key);
    return stored ? JSON.parse(stored) : null;
}

// Export utilities
window.FichaFacilUtils = {
    getGeolocation,
    formatDate,
    formatTime,
    formatDateTime,
    formatDistance,
    showToast,
    showLoading,
    hideLoading,
    playSound,
    getTodayISO,
    getDateDaysAgo,
    debounce,
    storeLastFichaje,
    getStoredLastFichaje,
    storeSession,
    getSession
};

})(); // Fin IIFE
