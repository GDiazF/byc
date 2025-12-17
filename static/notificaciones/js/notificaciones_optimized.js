/**
 * ============================================================================
 * JAVASCRIPT OPTIMIZADO PARA NOTIFICACIONES (SIN SSE, LAZY LOADING)
 * ============================================================================
 * Versión optimizada que:
 * - NO usa SSE (Server-Sent Events)
 * - Lazy loading: Solo carga notificaciones al hacer clic en la campanita
 * - Polling espaciado: Actualiza contador cada 60 segundos
 * - Usa caché del backend para evitar queries innecesarias
 * ============================================================================
 */

(function() {
    'use strict';
    
    let ultimoContador = null;
    let notificacionesCargadas = false;
    let pollingInterval = null;
    
    /**
     * Carga las notificaciones desde la API (solo cuando se abre el dropdown).
     */
    function cargarNotificaciones() {
        fetch('/notificaciones/api/?limit=10&archiviada=false')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    actualizarDropdown(data.notificaciones);
                    notificacionesCargadas = true;
                }
            })
            .catch(error => {
                console.error('Error al cargar notificaciones:', error);
            });
    }
    
    /**
     * Actualiza el badge del contador de notificaciones.
     */
    function actualizarBadge(count) {
        const badge = document.getElementById('notificationsBadge');
        if (badge) {
            const numCount = parseInt(count) || 0;
            
            if (numCount > 0) {
                badge.textContent = numCount > 99 ? '99+' : numCount.toString();
                badge.style.display = 'flex';
                badge.style.visibility = 'visible';
            } else {
                badge.style.display = 'none';
                badge.style.visibility = 'hidden';
            }
        }
    }
    
    /**
     * Actualiza el contador desde el servidor (usa caché del backend).
     */
    function actualizarContadorDesdeServidor() {
        return fetch('/notificaciones/api/contar/')
            .then(response => response.json())
            .then(data => {
                if (data.success !== undefined && data.success) {
                    const count = parseInt(data.count) || 0;
                    actualizarBadge(count);
                    ultimoContador = count;
                    return count;
                }
                return ultimoContador || 0;
            })
            .catch(error => {
                console.error('Error al actualizar contador:', error);
                return ultimoContador || 0;
            });
    }
    
    /**
     * Actualiza el dropdown con las notificaciones.
     */
    function actualizarDropdown(notificaciones) {
        const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
        if (!dropdownMenu) return;
        
        // Buscar el contenedor de notificaciones
        let container = dropdownMenu.querySelector('.notifications-list');
        if (!container) {
            const emptyMessage = dropdownMenu.querySelector('.dropdown-text-muted')?.parentElement;
            if (emptyMessage) {
                container = document.createElement('div');
                container.className = 'notifications-list';
                emptyMessage.replaceWith(container);
            }
        }
        
        if (!container) return;
        
        // Limpiar contenedor
        container.innerHTML = '';
        
        if (notificaciones.length === 0) {
            container.innerHTML = '<li class="px-3 py-2 text-center text-muted dropdown-text-muted">No hay notificaciones</li>';
            return;
        }
        
        // Renderizar notificaciones
        notificaciones.forEach(notif => {
            const item = document.createElement('li');
            item.className = `dropdown-item notification-item ${notif.leida ? 'leida' : 'no-leida'}`;
            item.style.cursor = 'pointer';
            
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <strong>${escapeHtml(notif.titulo)}</strong>
                        <p class="mb-1 small">${escapeHtml(notif.mensaje)}</p>
                        <small class="text-muted">${notif.fecha_creacion}</small>
                    </div>
                    ${!notif.leida ? '<span class="badge bg-primary ms-2">Nueva</span>' : ''}
                </div>
            `;
            
            // Marcar como leída al hacer clic
            item.addEventListener('click', function() {
                if (!notif.leida) {
                    marcarComoLeida(notif.id);
                }
            });
            
            container.appendChild(item);
        });
    }
    
    /**
     * Marca una notificación como leída.
     */
    function marcarComoLeida(notificacionId) {
        fetch(`/notificaciones/api/${notificacionId}/marcar-leida/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarBadge(data.count);
                cargarNotificaciones(); // Recargar lista
            }
        })
        .catch(error => {
            console.error('Error al marcar como leída:', error);
        });
    }
    
    /**
     * Marca todas las notificaciones como leídas.
     */
    function marcarTodasComoLeidas() {
        fetch('/notificaciones/api/marcar-todas-leidas/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarBadge(0);
                cargarNotificaciones(); // Recargar lista
            }
        })
        .catch(error => {
            console.error('Error al marcar todas como leídas:', error);
        });
    }
    
    /**
     * Escapa HTML para prevenir XSS.
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Obtiene el valor de una cookie.
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    /**
     * Inicia polling espaciado (cada 60 segundos) solo del contador.
     */
    function iniciarPolling() {
        // Polling cada 60 segundos (mucho menos agresivo)
        pollingInterval = setInterval(function() {
            actualizarContadorDesdeServidor().then(function(count) {
                // Si cambió el contador y el dropdown está cerrado, solo actualizar el badge
                // Si está abierto, recargar notificaciones
                const dropdownMenu = document.querySelector('#notificationsDropdown + .dropdown-menu');
                const isOpen = dropdownMenu && dropdownMenu.classList.contains('show');
                
                if (isOpen && count !== ultimoContador) {
                    cargarNotificaciones();
                }
            });
        }, 60000); // 60 segundos
    }
    
    /**
     * Inicialización al cargar la página.
     */
    function inicializar() {
        // Solo cargar el contador inicialmente (sin notificaciones)
        actualizarContadorDesdeServidor();
        
        // Lazy loading: Cargar notificaciones solo cuando se abre el dropdown
        const dropdown = document.getElementById('notificationsDropdown');
        if (dropdown) {
            dropdown.addEventListener('click', function() {
                if (!notificacionesCargadas) {
                    cargarNotificaciones();
                }
            });
        }
        
        // Botón de marcar todas como leídas
        const btnMarcarTodas = document.getElementById('btnMarcarTodasLeidasDropdown');
        if (btnMarcarTodas) {
            btnMarcarTodas.addEventListener('click', function(e) {
                e.preventDefault();
                marcarTodasComoLeidas();
            });
        }
        
        // Iniciar polling espaciado
        iniciarPolling();
        
        console.log('✅ Sistema de notificaciones optimizado iniciado (sin SSE, polling cada 60s)');
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }
    
    // Limpiar interval al salir de la página
    window.addEventListener('beforeunload', function() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });
    
})();

