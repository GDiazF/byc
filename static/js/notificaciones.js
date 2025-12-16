/**
 * Sistema global de notificaciones para errores y mensajes
 * 
 * Este archivo proporciona funciones para mostrar notificaciones elegantes
 * en lugar de usar alert() del navegador, especialmente para errores de permisos.
 */

/**
 * Muestra una notificación elegante usando Bootstrap alerts
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duración en milisegundos (default: 5000)
 */
function showNotification(message, type = 'success', duration = 5000) {
    // Crear contenedor de alertas si no existe
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    // Mapear tipos a clases de Bootstrap
    const typeMap = {
        'success': { class: 'alert-success', icon: 'check-circle' },
        'error': { class: 'alert-danger', icon: 'exclamation-triangle' },
        'warning': { class: 'alert-warning', icon: 'exclamation-circle' },
        'info': { class: 'alert-info', icon: 'info-circle' }
    };
    
    const alertConfig = typeMap[type] || typeMap['error'];
    
    // Crear el alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertConfig.class} alert-dismissible fade show alert-permanent`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.marginBottom = '10px';
    alertDiv.innerHTML = `
        <i class="bi bi-${alertConfig.icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Agregar al contenedor
    container.appendChild(alertDiv);
    
    // Auto-cerrar después de la duración especificada
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150); // Tiempo de la animación fade de Bootstrap
    }, duration);
}

/**
 * Maneja errores de respuesta AJAX de manera consistente
 * Detecta errores de permisos (403) y otros errores HTTP
 * @param {Response} response - Objeto Response de fetch
 * @returns {Promise} Promise que resuelve con los datos JSON o lanza un error
 */
async function handleAjaxResponse(response) {
    // Intentar parsear la respuesta como JSON
    let data;
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    
    if (isJson) {
        try {
            data = await response.json();
        } catch (e) {
            // Si falla el parseo JSON, crear un objeto de error genérico
            data = {
                status: 'error',
                message: `Error ${response.status}: ${response.statusText}`
            };
        }
    } else {
        // Si no es JSON, crear un objeto de error genérico
        data = {
            status: 'error',
            message: `Error ${response.status}: ${response.statusText}`
        };
    }
    
    // Si la respuesta no es exitosa, mostrar error
    if (!response.ok) {
        // Errores de permisos (403)
        if (response.status === 403) {
            showNotification(
                data.message || data.error || 'No tiene permiso para realizar esta acción',
                'error',
                6000 // Mostrar por más tiempo los errores de permisos
            );
        }
        // Errores de autenticación (401)
        else if (response.status === 401) {
            showNotification(
                data.message || 'Su sesión ha expirado. Por favor, inicie sesión nuevamente.',
                'warning',
                6000
            );
        }
        // Otros errores
        else {
            showNotification(
                data.message || data.error || `Error ${response.status}: ${response.statusText}`,
                'error',
                5000
            );
        }
        
        // Lanzar error para que pueda ser capturado por .catch()
        throw new Error(data.message || data.error || `Error ${response.status}`);
    }
    
    // Si hay un error en los datos (aunque el status sea 200)
    if (data.status === 'error') {
        showNotification(
            data.message || data.error || 'Error al procesar la solicitud',
            'error',
            5000
        );
        throw new Error(data.message || data.error || 'Error al procesar la solicitud');
    }
    
    return data;
}

/**
 * Función helper para hacer peticiones fetch con manejo automático de errores
 * @param {string} url - URL a la que hacer la petición
 * @param {object} options - Opciones para fetch (method, headers, body, etc.)
 * @returns {Promise} Promise que resuelve con los datos o muestra error automáticamente
 */
async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await handleAjaxResponse(response);
        return data;
    } catch (error) {
        // El error ya fue manejado por handleAjaxResponse, solo loguear
        console.error('Error en fetch:', error);
        throw error;
    }
}

