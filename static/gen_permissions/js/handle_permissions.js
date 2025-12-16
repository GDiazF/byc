/**
 * Manejo global de errores de permisos en peticiones AJAX.
 * 
 * Este script intercepta todas las respuestas AJAX con codigo 403 (Forbidden)
 * y muestra un mensaje amigable al usuario en lugar de dejar que el navegador
 * muestre un error generico.
 * 
 * Funciona con:
 * - jQuery AJAX (si esta disponible)
 * - Fetch API nativa
 * - XMLHttpRequest nativo
 */

(function() {
    'use strict';
    
    // Mensaje generico para errores de permisos
    const PERMISSION_DENIED_MESSAGE = 'No tiene permiso para realizar esta accion. Por favor, contacte al administrador si necesita acceso.';
    
    /**
     * Muestra un alert con el mensaje de error de permisos.
     * 
     * @param {string} message - Mensaje de error a mostrar. Si no se proporciona,
     *                          se usa el mensaje genérico.
     */
    function showPermissionAlert(message) {
        // Intentar usar el mensaje personalizado si esta disponible, sino usar el generico
        const alertMessage = message || PERMISSION_DENIED_MESSAGE;
        alert(alertMessage);
    }
    
    /**
     * Extrae el mensaje de error de una respuesta JSON.
     * 
     * Intenta obtener el mensaje de diferentes campos posibles en la respuesta
     * (message, error, detail, statusText) y retorna un mensaje genérico si no encuentra ninguno.
     * 
     * @param {Object|string} response - Respuesta JSON o string con el error.
     * @returns {string} Mensaje de error extraído o mensaje genérico.
     */
    function extractErrorMessage(response) {
        if (response && typeof response === 'object') {
            // Intentar obtener el mensaje de diferentes formatos posibles
            return response.message || 
                   response.error || 
                   response.detail || 
                   response.statusText || 
                   PERMISSION_DENIED_MESSAGE;
        }
        return PERMISSION_DENIED_MESSAGE;
    }
    
    /**
     * Maneja errores 403 en respuestas AJAX.
     * 
     * Extrae el mensaje de error de la respuesta y muestra un alert al usuario.
     * 
     * @param {XMLHttpRequest} xhr - Objeto XMLHttpRequest de la petición.
     * @param {Object|string} response - Respuesta de la petición (JSON o string).
     * @returns {boolean} True si se manejó el error, False en caso contrario.
     */
    function handle403Error(xhr, response) {
        if (xhr.status === 403) {
            let errorMessage = PERMISSION_DENIED_MESSAGE;
            
            // Intentar parsear la respuesta JSON
            try {
                if (typeof response === 'string') {
                    const jsonResponse = JSON.parse(response);
                    errorMessage = extractErrorMessage(jsonResponse);
                } else if (typeof response === 'object') {
                    errorMessage = extractErrorMessage(response);
                }
            } catch (e) {
                // Si no se puede parsear, usar el mensaje generico
                console.warn('No se pudo parsear la respuesta de error:', e);
            }
            
            showPermissionAlert(errorMessage);
            return true; // Indicar que se manejo el error
        }
        return false; // No se manejo el error
    }
    
    // ============================================================================
    // Interceptar jQuery AJAX (si jQuery esta disponible)
    // ============================================================================
    if (typeof jQuery !== 'undefined') {
        // Interceptar todas las peticiones AJAX de jQuery
        jQuery(document).ajaxError(function(event, xhr, settings, thrownError) {
            if (xhr.status === 403) {
                let errorMessage = PERMISSION_DENIED_MESSAGE;
                
                try {
                    const response = xhr.responseJSON || JSON.parse(xhr.responseText);
                    errorMessage = extractErrorMessage(response);
                } catch (e) {
                    // Usar mensaje generico si no se puede parsear
                }
                
                showPermissionAlert(errorMessage);
                event.preventDefault(); // Prevenir el manejo de error por defecto
            }
        });
        
        console.log('[Permisos] Interceptor jQuery AJAX cargado');
    }
    
    // ============================================================================
    // Interceptar Fetch API nativa
    // ============================================================================
    if (typeof fetch !== 'undefined') {
        const originalFetch = window.fetch;
        
        window.fetch = function(...args) {
            return originalFetch.apply(this, args)
                .then(function(response) {
                    // Si es un error 403, interceptar antes de que se procese
                    if (response.status === 403) {
                        // Clonar la respuesta para poder leerla multiples veces
                        const clonedResponse = response.clone();
                        
                        // Intentar leer el JSON de la respuesta
                        clonedResponse.json()
                            .then(function(data) {
                                const errorMessage = extractErrorMessage(data);
                                showPermissionAlert(errorMessage);
                            })
                            .catch(function() {
                                // Si no es JSON, usar mensaje generico
                                showPermissionAlert(PERMISSION_DENIED_MESSAGE);
                            });
                        
                        // Retornar la respuesta original para que el codigo que hizo la peticion
                        // tambien pueda manejarla si es necesario
                        return response;
                    }
                    return response;
                })
                .catch(function(error) {
                    // Manejar otros errores si es necesario
                    console.error('[Permisos] Error en fetch:', error);
                    throw error;
                });
        };
        
        console.log('[Permisos] Interceptor Fetch API cargado');
    }
    
    // ============================================================================
    // Interceptar XMLHttpRequest nativo
    // ============================================================================
    if (typeof XMLHttpRequest !== 'undefined') {
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
            this._url = url;
            return originalOpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function(data) {
            const xhr = this;
            
            // Agregar listener para cuando la peticion termine
            xhr.addEventListener('loadend', function() {
                if (xhr.status === 403) {
                    let errorMessage = PERMISSION_DENIED_MESSAGE;
                    
                    try {
                        const response = JSON.parse(xhr.responseText);
                        errorMessage = extractErrorMessage(response);
                    } catch (e) {
                        // Usar mensaje generico si no se puede parsear
                    }
                    
                    showPermissionAlert(errorMessage);
                }
            });
            
            return originalSend.apply(this, arguments);
        };
        
        console.log('[Permisos] Interceptor XMLHttpRequest cargado');
    }
    
    console.log('[Permisos] Sistema de manejo de errores de permisos inicializado');
})();


