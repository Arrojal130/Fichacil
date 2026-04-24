/**
 * FichaFácil MVP - API Client
 * Handles all communication with the backend.
 */

// Encapsulado en IIFE para evitar polución del scope global
(function() {
'use strict';

// API Base URL - direct backend for local/LAN, proxy path in production
const LOCAL_HOSTNAMES = new Set(['localhost', '127.0.0.1']);
const PRIVATE_IP_REGEX = /^(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[0-1])\.)/;
const IS_LOCAL_OR_LAN_HOST = LOCAL_HOSTNAMES.has(window.location.hostname) || PRIVATE_IP_REGEX.test(window.location.hostname);
const API_BASE = IS_LOCAL_OR_LAN_HOST
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : '/api';

console.log('🔌 API Configuration:');
console.log('   Frontend:', window.location.origin);
console.log('   Backend API_BASE:', API_BASE);
console.log('   Hostname:', window.location.hostname);

/**
 * Make an API request with error handling.
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for JWT
    };
    
    // Merge options
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    // Add auth token if exists
    const token = localStorage.getItem('token');
    if (token) {
        finalOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        console.log('🌐 API Request:', {
            method: finalOptions.method || 'GET',
            url: url,
            hasToken: !!token
        });
        
        const response = await fetch(url, finalOptions);
        
        console.log('📡 API Response:', {
            url: url,
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });
        
        // Handle non-JSON responses (like PDF)
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/pdf')) {
            if (!response.ok) throw new Error('Error descargando PDF');
            return response.blob();
        }
        
        // Parse JSON
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Error parsing JSON:', jsonError);
            if (!response.ok) {
                throw new Error(`Error HTTP ${response.status}: ${response.statusText}`);
            }
            throw new Error('Respuesta inválida del servidor');
        }
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Error en la solicitud');
        }
        
        return data;
    } catch (error) {
        console.error('❌ API Error:', {
            message: error.message,
            url: url,
            method: finalOptions.method || 'GET',
            error: error
        });
        
        // Check if it's a network error (can't reach backend)
        if (error.message.includes('fetch') || error.message.includes('NetworkError') || error instanceof TypeError) {
            console.error('🔴 Network Error: Cannot reach backend at', API_BASE);
            console.error('   - Check if backend is running: uvicorn app.main:app --host 0.0.0.0 --port 8000');
            console.error('   - Check if PC IP is correct:', window.location.hostname);
            throw new Error('No se ha podido contactar con FichaFácil. El fichaje no se ha registrado todavía. Reintenta en unos segundos.');
        }
        
        throw error;
    }
}

/**
 * Auth API
 */
const authAPI = {
    // Register new business with admin
    async register(data) {
        const result = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        localStorage.setItem('token', result.access_token);
        return result;
    },
    
    // Admin login
    async loginAdmin(email, password) {
        const result = await apiRequest('/auth/login/admin', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        localStorage.setItem('token', result.access_token);
        return result;
    },
    
    // Employee login (returns token but usually not stored)
    async loginEmpleado(negocioId, pin) {
        const result = await apiRequest('/auth/login/empleado', {
            method: 'POST',
            body: JSON.stringify({ negocio_id: negocioId, pin: pin }),
        });
        return result;
    },
    
    // Get current user
    async me() {
        return await apiRequest('/auth/me');
    },
    
    // Logout
    async logout() {
        await apiRequest('/auth/logout', { method: 'POST' });
        localStorage.removeItem('token');
    },
    
    // Check if logged in
    isLoggedIn() {
        return !!localStorage.getItem('token');
    }
};

/**
 * Negocios API
 */
const negociosAPI = {
    // Search businesses (public)
    async search(query = '') {
        return await apiRequest(`/negocios/search?q=${encodeURIComponent(query)}`);
    },
    
    // Get my business
    async getMine() {
        return await apiRequest('/negocios/me');
    },
    
    // Update my business
    async update(data) {
        return await apiRequest('/negocios/me', {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },
    
    // List employees
    async listEmpleados() {
        return await apiRequest('/negocios/empleados');
    },
    
    // Create employee
    async createEmpleado(data) {
        return await apiRequest('/negocios/empleados', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },
    
    // Update employee
    async updateEmpleado(id, data) {
        const params = new URLSearchParams();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                params.append(key, value);
            }
        });
        return await apiRequest(`/negocios/empleados/${id}?${params}`, {
            method: 'PATCH',
        });
    },
    
    // Deactivate employee
    async deactivateEmpleado(id) {
        return await apiRequest(`/negocios/empleados/${id}`, {
            method: 'DELETE',
        });
    }
};

/**
 * Fichajes API
 */
const fichajesAPI = {
    // Create fichaje (employee)
    async fichar(negocioId, pin, tipo, lat = null, lon = null) {
        return await apiRequest('/fichajes/', {
            method: 'POST',
            body: JSON.stringify({
                negocio_id: negocioId,
                pin: pin,
                tipo: tipo, // "ENTRADA" or "SALIDA"
                lat: lat,
                lon: lon,
            }),
        });
    },
    
    // Get last fichaje
    async getUltimo(negocioId, pin) {
        return await apiRequest('/fichajes/ultimo', {
            method: 'POST',
            body: JSON.stringify({ negocio_id: negocioId, pin: pin }),
        });
    },
    
    // Get today's fichajes (admin)
    async getHoy() {
        return await apiRequest('/fichajes/hoy');
    },
    
    // Get fichajes for date range (admin)
    async getRango(fechaInicio, fechaFin, empleadoId = null) {
        let url = `/fichajes/rango?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
        if (empleadoId) url += `&empleado_id=${empleadoId}`;
        return await apiRequest(url);
    },
    
    // Get fichaje history for employee (PIN auth)
    async getHistorialEmpleado(negocioId, pin, dias = 7) {
        return await apiRequest('/fichajes/historial-empleado', {
            method: 'POST',
            body: JSON.stringify({ negocio_id: negocioId, pin: pin, dias: dias }),
        });
    }
};

/**
 * Correcciones API
 */
const correccionesAPI = {
    // Create correction
    async crear(data) {
        return await apiRequest('/correcciones/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },
    
    // Get pending corrections
    async getPendientes() {
        return await apiRequest('/correcciones/pendientes');
    },
    
    // Approve/reject correction
    async aprobar(id, pin, aprobar) {
        return await apiRequest(`/correcciones/${id}/aprobar`, {
            method: 'POST',
            body: JSON.stringify({ pin, aprobar }),
        });
    },
    
    // Get history
    async getHistorial(empleadoId = null) {
        let url = '/correcciones/historial';
        if (empleadoId) url += `?empleado_id=${empleadoId}`;
        return await apiRequest(url);
    },
    
    // ========================================
    // EMPLOYEE METHODS (PIN authentication, no JWT)
    // ========================================
    
    // Get pending corrections for employee (PIN auth)
    async getPendientesEmpleado(negocioId, pin) {
        return await apiRequest('/correcciones/pendientes-empleado', {
            method: 'POST',
            body: JSON.stringify({ negocio_id: negocioId, pin: pin }),
        });
    },
    
    // Approve/reject correction as employee (PIN auth)
    async aprobarEmpleado(correccionId, negocioId, pin, aprobar) {
        return await apiRequest(`/correcciones/${correccionId}/aprobar-empleado`, {
            method: 'POST',
            body: JSON.stringify({ 
                negocio_id: negocioId, 
                pin: pin, 
                aprobar: aprobar 
            }),
        });
    }
};

/**
 * PDF API
 */
const pdfAPI = {
    // Generate and download PDF
    async download(fechaInicio, fechaFin, empleadoId = null) {
        let url = `/pdf/registro?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
        if (empleadoId) url += `&empleado_id=${empleadoId}`;
        
        const blob = await apiRequest(url);
        
        // Create download link
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `registro_${fechaInicio}_${fechaFin}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
    }
};

/**
 * SSE Realtime connection
 */
function connectSSE(negocioId, onEvent) {
    const url = `${API_BASE}/sse/${negocioId}`;
    const eventSource = new EventSource(url);
    
    eventSource.onopen = () => {
        console.log('✅ SSE connected');
    };
    
    eventSource.onerror = (error) => {
        console.error('❌ SSE error:', error);
        // Reconnect after 5 seconds
        setTimeout(() => {
            eventSource.close();
            connectSSE(negocioId, onEvent);
        }, 5000);
    };
    
    eventSource.addEventListener('fichaje', (event) => {
        const data = JSON.parse(event.data);
        onEvent('fichaje', data);
    });
    
    eventSource.addEventListener('correccion', (event) => {
        const data = JSON.parse(event.data);
        onEvent('correccion', data);
    });
    
    eventSource.addEventListener('ping', () => {
        console.log('🏓 SSE ping');
    });
    
    return eventSource;
}

// Export for use in other scripts
window.FichaFacilAPI = {
    auth: authAPI,
    negocios: negociosAPI,
    fichajes: fichajesAPI,
    correcciones: correccionesAPI,
    pdf: pdfAPI,
    connectSSE,
};

})(); // Fin IIFE
